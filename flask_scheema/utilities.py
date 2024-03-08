import os
import random
import re
import socket
from typing import Optional, Any, Dict, List

from flask import Flask, current_app
from jinja2 import Environment, FileSystemLoader
from marshmallow import Schema
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

from flask_scheema.logging import logger
from flask_scheema.specification.doc_generation import (
    make_endpoint_description,
)


class AttributeInitializerMixin:
    """
    Mixin class to initialise class attributes from the Flask app config and kwargs.
    """

    def __init__(self, app: Flask, *args, **kwargs):
        """
        Initializes the object attributes for the classes.

        Args:
            app (Flask): The flask app.
            *args (list): List of arguments.
            **kwargs (dict): Dictionary of keyword arguments.

        """

        self._set_class_attributes(**kwargs)
        self._set_app_config_attributes(app)
        super().__init__()

    def _set_app_config_attributes(self, app: Flask):
        """
        Sets the class attributes from the app config if they exist in uppercase in the config
        and in lowercase in the class.

        i.e  APP_URL (in config) == app_url (in the class)

        Args:
            app (Flask): The Flask app instance containing the configuration.

        """
        for key in vars(type(self)).keys():
            if key.startswith("__"):
                continue  # Skip special methods

            # Convert the class attribute name to uppercase to match the Flask config keys
            config_key = key.upper()
            has_underline = False
            if config_key.startswith("_"):
                config_key = config_key[1:]
                has_underline = True

            # Check if this key exists in the Flask app's config
            if config_key in app.config:
                if has_underline:
                    # If the class attribute name starts with an underscore, set the value to the config value
                    setattr(self, key, "_" + app.config[config_key])
                else:
                    setattr(self, key, app.config[config_key])

            else:
                # Optionally, you can set it to None or keep the existing value
                # setattr(self, key, None)
                pass

    def _set_class_attributes(self, **kwargs):
        """
        Sets the class attributes from the keyword arguments if they exist.

        Args:
            **kwargs (dict): Dictionary of keyword arguments.

        Returns:

        """
        for key in vars(type(self)).keys():
            if key.startswith("__"):
                continue  # Skip special methods
            if key in kwargs:
                setattr(self, key, kwargs[key])


def normalize_key(key: str) -> str:
    """
    Normalize the key to handle different cases.

    Args:
        key (str): The original key.

    Returns:
        str: The normalized key.
    """
    # Convert to uppercase
    return key.upper()

def get_config_or_model_meta(
        key: str,
        model: Optional[DeclarativeBase] = None,
        output_schema: Optional[Schema] = None,
        input_schema: Optional[Schema] = None,
        default=None,
        allow_join=False,
        method="IGNORE",
) -> Any:
    """
    Dynamically gets the configuration or Meta attribute from the model, or schemas,
    with precedence to models and schemas over Flask config, for any given key.
    """
    from flask import current_app  # Assuming Flask context is available

    def normalize_key(key: str) -> str:
        """Normalizes the key for consistent access patterns."""
        return key.lower()

    def generate_method_based_keys(base_key: str) -> List[str]:
        """Generates method-based keys based on the base key."""
        methods = ["get", "get", "post", "put", "patch", "delete"]
        return [f"{meth}_{base_key}" for meth in methods if method.lower() in meth]

    def search_in_sources(sources, keys):
        """
        Searches for keys in given models or schemas more efficiently and safely.
        """
        out = []
        for source in sources:
            if source is not None:
                meta = getattr(source, 'Meta', None)
                if meta is not None:
                    for key in keys:
                        result = getattr(meta, key, None)

                        if isinstance(result, list) and allow_join:
                            out.extend(result)
                        if result is not None:
                            return result

        if allow_join:
            return out
        return None

    def search_in_flask_config(keys):
        """Searches for keys in Flask config."""
        app = current_app
        for key in keys:
            conf_val = app.config.get(key.upper() if "API_" in key.upper() else "API_" + key.upper())
            if conf_val is not None:
                return conf_val
        return None

    normalized_key = normalize_key(key)
    method_based_keys = generate_method_based_keys(normalized_key.replace("api_", ""))

    # Sources and keys setup
    sources = [model, output_schema, input_schema]
    keys_for_sources = method_based_keys + [normalized_key, normalize_key(key).replace("api_", "")]
    keys_for_config = method_based_keys + [normalized_key]

    # 1st & 2nd: Search in models and schemas
    result = search_in_sources(sources, keys_for_sources)
    if result is not None and result != []:
        return result

    # 3rd & 4th: Search in Flask config
    result = search_in_flask_config(keys_for_config)
    if result is not None and result != []:
        return result

    return default

# def get_config_or_model_meta(
#         key: str,
#         model: Optional[DeclarativeBase] = None,
#         output_schema: Optional[Schema] = None,
#         input_schema: Optional[Schema] = None,
#         default=None,
#         allow_join=False,
#         method="GET",
# ) -> Any:
#     """
#     Gets the configuration or Meta attribute from the model, or schemas, with precedence to models and schemas over Flask config.
#     """
#     from flask_scheema.api.utils import get_models_relationships
#
#     normalized_key = normalize_key(key)  # Used for Flask config
#     values_to_join = []
#     methods_to_check = ["get_one", "get_many", "post", "put", "patch", "delete"] + ["get_" + x["model"].__name__.lower() for x in get_models_relationships(model)]
#
#
#     # Helper function for processing Meta attributes, considering both original and normalized keys
#     def process_meta_attribute(source, original_key, normalized_key, allow_join, values_to_join):
#         # Try accessing with the original case first
#         meta_value = get_nested_attr(source, f"Meta.{original_key}", default=None)
#         if meta_value is None:
#             # If not found, try with the normalized key
#             meta_value = get_nested_attr(source, f"Meta.{normalized_key}", default=None)
#
#         if meta_value is not None:
#             if allow_join and isinstance(meta_value, list):
#                 values_to_join.extend(meta_value)
#             elif not allow_join:
#                 return meta_value
#         return None
#
#     # Attempt to retrieve the value from models and schemas first, using both original and normalized keys
#     for source in (model, output_schema, input_schema):
#         if source is not None:
#             result = process_meta_attribute(source, key, normalized_key, allow_join, values_to_join)
#             if result is not None:
#                 return result
#
#     # Helper function to try accessing Flask config with and without 'API_' prefix
#     def try_get_config(normalized_key):
#         app = current_app
#         conf_val = app.config.get(normalized_key.upper())  # Flask config keys are typically uppercase
#         if conf_val is not None:
#             return conf_val
#         return None
#
#     # Check Flask config if the value was not found in models or schemas
#     config_value = try_get_config(normalized_key)
#     if config_value is not None:
#         if allow_join and isinstance(config_value, list):
#             values_to_join.extend(config_value)
#         else:
#             return config_value
#
#     # If allow_join is True and lists were collected, return the joined list
#     if allow_join and values_to_join:
#         return values_to_join
#
#     # Return default if none of the above
#     return default


def scrape_extra_info_from_spec_data(
        spec_data: Dict[str, Any],
        method: str,
        multiple: bool = False,
) -> Dict[str, Any]:
    """
    Scrapes the extra info from the spec data and returns it as a dictionary.

    Args:
        spec_data (dict): The spec data.
        method (str): The HTTP method.
        multiple (bool, optional): Whether the endpoint returns multiple items. Defaults to False.

    Returns:
        dict: The extra info.
    """

    # Extract required data from spec_data
    model = spec_data.get("model")
    output_schema = spec_data.get("output_schema")
    input_schema = spec_data.get("input_schema")
    function = spec_data.get("function")

    # Error handling for missing keys
    # Error handling for missing keys
    if not all([model, output_schema or input_schema, method, function]):
        logger.log(1, "Missing data for documentation generation")

    # Get tag information
    # todo check here for the tag in documentation, needs to pull from the model.
    spec_data["tag"] = get_config_or_model_meta(
        "tag", model, output_schema, input_schema, "UNKNOWN"
    )

    # Generate summary based on AUTO_NAME_ENDPOINTS configuration
    if get_config_or_model_meta("AUTO_NAME_ENDPOINTS", default=True):
        schema = spec_data.get("output_schema") or spec_data.get("input_schema")
        if schema:
            spec_data["summary"] = make_endpoint_description(
                schema, method, **spec_data
            )

    # Extract summary and description from function docstring
    if function.__doc__:
        parts = function.__doc__.strip().split("---", 1)
        spec_data["summary"] = spec_data.get("summary") or parts[0].strip()
        if len(parts) > 1:
            spec_data["description"] = parts[1].strip()

    # Get description information
    if method.lower() == "get" and multiple:
        config_val = f"{method.lower()}_many_description"
    elif method.lower() == "get" and not multiple:
        config_val = f"{method.lower()}_single_description"
    else:
        config_val = f"{method.lower()}_description"

    new_desc = get_config_or_model_meta(
        config_val, model, output_schema, input_schema, None
    )
    if new_desc:
        spec_data["description"] = new_desc

    return spec_data


def manual_render_absolute_template(absolute_template_path, **kwargs):
    """
    Render a template manually given its absolute path.

    Args:
        absolute_template_path (str): The absolute path to the template.
        **kwargs: Additional keyword arguments to pass to the template.

    Returns:
        str: The rendered template.
    """
    # Calculate the directory containing the template
    template_dir = os.path.dirname(absolute_template_path)

    # Calculate the relative path from the Flask app's root path
    additional_path = os.path.relpath(template_dir, current_app.root_path)

    # Set up the Environment and Loader
    template_folder = os.path.join(current_app.root_path, additional_path)
    env = Environment(loader=FileSystemLoader(template_folder))

    # Extract the template filename from the absolute path
    template_filename = os.path.basename(absolute_template_path)

    # Load and render the template
    template = env.get_template(template_filename)
    return template.render(**kwargs)


def extract_relationships(model, randomise=True):
    """
    Extract relationships from a SQLAlchemy model, if randomise is True, the order of the relationships will be randomised.
    """
    relationships = []
    inspector = inspect(model)

    for relationship in inspector.relationships:
        relationships.append(relationship.mapper.class_)

    randomise and random.shuffle(relationships)

    return relationships


def extract_sqlalchemy_columns(model, randomise=True):
    """
    Extract column names from a SQLAlchemy model, if randomise is True, the order of the columns will be randomised.

    Args:
        model (SQLAlchemy model): SQLAlchemy model to extract columns from.
        randomise (bool, optional): Whether to randomise the order of the columns. Defaults to True.

    Returns:
        List[str]: List of column names.
    """

    columns = inspect(model)
    model_columns = [x.name for x in list(columns.mapper.columns)]
    randomise and random.shuffle(model_columns)
    return model_columns


def find_child_from_parent_dir(parent, child, current_dir=os.getcwd()):
    """Recursively finds the path to the child directory in the parent directory.


    Args:
        parent: The path to the parent directory.
        child: The name of the child directory.
        current_dir: The current directory to start the search from.

    Returns:
        The path to the child directory, or None if the child directory is not found.
    """

    if os.path.basename(current_dir) == parent:
        for dirname in os.listdir(current_dir):
            if dirname == child:
                return os.path.join(current_dir, dirname)

    for dirname in os.listdir(current_dir):
        if dirname.startswith("."):
            continue
        if dirname == "node_modules":
            continue

        child_dir_path = os.path.join(current_dir, dirname)
        if os.path.isdir(child_dir_path):
            child_dir_path = find_child_from_parent_dir(parent, child, child_dir_path)
            if child_dir_path is not None:
                return child_dir_path

    return None

def check_prerequisites(service):
    """
    Checks if the necessary prerequisites for a given service are available.
    Args:
        service: The name of the service (Memcached, Redis, MongoDB).
    Raises:
        ImportError: If the prerequisite library for the service is not installed.
    """

    back_end_spec = "or specify a cache service URI in the flask configuration with the key API_RATE_LIMIT_STORAGE_URI={URL}:{PORT}"
    if service == 'Memcached':
        try:
            import pymemcache
        except ImportError:
            raise ImportError("Memcached prerequisite not available. Please install pymemcache " + back_end_spec)
    elif service == 'Redis':
        try:
            import redis
        except ImportError:
            raise ImportError("Redis prerequisite not available. Please install redis-py " + back_end_spec)
    elif service == 'MongoDB':
        try:
            import pymongo
        except ImportError:
            raise ImportError("MongoDB prerequisite not available. Please install pymongo " + back_end_spec)

def check_services():
    """
    Checks if any of the following services are running on the local machine: Memcached, Redis, MongoDB.
    Also checks for the availability of required client libraries.
    Returns:
        Connection string of the available and correctly configured service.
    Raises:
        ImportError: If the required client library for the detected service is not installed.
    """
    services = {
        'Memcached': 11211,
        'Redis': 6379,
        'MongoDB': 27017,
    }
    uri = get_config_or_model_meta("API_RATE_LIMIT_STORAGE_URI", default=None)
    if uri:
        return uri

    for service, port in services.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)  # Set a timeout to avoid waiting too long
        try:
            s.connect(('127.0.0.1', port))
            s.close()
            # Before returning, check for prerequisites
            check_prerequisites(service)  # This will raise ImportError if the lib is not available
            if service == 'Memcached':
                return f'memcached://127.0.0.1:{port}'
            elif service == 'Redis':
                return f'redis://127.0.0.1:{port}'
            elif service == 'MongoDB':
                return f'mongodb://127.0.0.1:{port}'
        except (socket.error) as e:
            continue  # If connection fails or prerequisites are missing, move on to the next service

    return None


def validate_flask_limiter_rate_limit_string(rate_limit_str):
    """
    Validates a Flask-Limiter rate limit string, including more complex intervals like "10 per 5 minutes".

    Args:
        rate_limit_str (str): The rate limit string to validate.

    Returns:
        bool: True if the rate limit string is valid, False otherwise.
    """
    # This pattern matches strings like "10 per 5 minutes" or "1 per second".
    # It checks for a positive integer, followed by "per", another optional positive integer, and a time unit.
    pattern = re.compile(r'^\d+\s+per\s+(\d+\s+)?(second|minute|hour|day|seconds|minutes|hours|days)$', re.IGNORECASE)

    # Use the pattern to search the input string
    return bool(pattern.match(rate_limit_str))
