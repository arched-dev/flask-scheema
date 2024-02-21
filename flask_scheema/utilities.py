import os
import random
from typing import Optional, Any, Dict

from flask import Flask, current_app
from jinja2 import Environment, FileSystemLoader
from marshmallow import Schema
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

from flask_scheema.extensions import logger
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


def get_nested_attr(obj, nested_key: str, default=None) -> Any:
    keys = nested_key.split(".")
    for key in keys:
        if hasattr(obj, key):
            obj = getattr(obj, key)
        else:
            return default
    return obj


def get_config_or_model_meta(
    key: str,
    model: Optional[DeclarativeBase] = None,
    output_schema: Optional[Schema] = None,
    input_schema: Optional[Schema] = None,
    default=None,
) -> Any:
    """
    Used to get either the flask config or the Meta attribute from the model, or schemas.

    Args:
        key (str): The key to get.
        model (DeclarativeBase): The model to get the key from.
        output_schema (Schema): The output schema to get the key from.
        input_schema (Schema): The input schema to get the key from.
        default (Any): The default value to return if the key is not found.

    Returns:
        Any: The value of the key.
    """
    app = current_app

    # Check Flask config
    config_value = app.config.get(key.upper())
    if config_value is not None:
        return config_value

    # Check model Meta

    if model is not None:
        model_meta_value = get_nested_attr(model, f"Meta.{key}", default=None)
        if model_meta_value is not None:
            return model_meta_value

    # Check output_schema Meta
    if output_schema is not None:
        output_schema_meta_value = get_nested_attr(
            output_schema, f"Meta.{key}", default=None
        )
        if output_schema_meta_value is not None:
            return output_schema_meta_value

    # Check input_schema Meta
    if input_schema is not None:
        input_schema_meta_value = get_nested_attr(
            input_schema, f"Meta.{key}", default=None
        )
        if input_schema_meta_value is not None:
            return input_schema_meta_value

    # Return default if none of the above
    return default


def scrape_extra_info_from_spec_data(
    spec_data: Dict[str, Any], method: str
) -> Dict[str, Any]:
    """
    Scrapes the extra info from the spec data and returns it as a dictionary.

    Args:
        spec_data (dict): The spec data.

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
        logger.log(1, "Missing data for documentation generatio")

    # Get tag information
    #todo check here for the tag in documentation, needs to pull from the model.
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
    new_desc = get_config_or_model_meta(
        f"description.{method}", model, output_schema, input_schema, None
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


def find_root(path: str, search: str) -> str:
    """
    Recursively finds the path to the child directory in the parent directory.

    Args:
        path (str): The path to the parent directory.
        search (str): The name of the child directory.

    Returns:
        The path to the child directory, or None if the child directory is not found.
    """
    while True:
        paths = os.path.split(path)
        if paths[1] == search:
            return path
        else:
            path = paths[0]
            if path == "/":
                return None
