import importlib
import os
from functools import wraps
from typing import Optional, List, Type, Callable

from apispec import APISpec
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema
from sqlalchemy.orm import DeclarativeBase

from flask_scheema.api.api import RiceAPI
from flask_scheema.api.decorators import handle_many, handle_one
from flask_scheema.logging import logger
from flask_scheema.specification.doc_generation import get_rule
from flask_scheema.specification.specification import (
    CurrySpec,
)
from flask_scheema.utilities import (
    AttributeInitializerMixin, check_services, get_config_or_model_meta, validate_flask_limiter_rate_limit_string,
)

FLASK_APP_NAME = "flask_scheema"


class Naan(AttributeInitializerMixin):
    app: Flask
    api_spec: Optional[CurrySpec] = None  # The api spec object
    api: Optional[RiceAPI] = None  # The api spec object
    base_dir: str = os.path.dirname(os.path.abspath(__file__))
    route_spec: List = (
        []
    )  # list of routes to specify, they come from the decorator or todo: auto discovery
    limiter: Limiter

    def __init__(self, app: Optional[Flask] = None, *args, **kwargs):
        """
                Initializes the Naan object.


        Args:
            app (Flask): The flask app.
            *args (list): List of arguments.
            **kwargs (dict): Dictionary of keyword arguments.

        Returns:
            None

        """
        if app is not None:
            self.init_app(app, *args, **kwargs)
            logger.verbosity_level = self.get_config("API_VERBOSITY_LEVEL", 0)

    def init_app(self, app: Flask, *args, **kwargs):
        """
                Initializes the Naan object.


        Args:
            app (Flask): The flask app.
            *args (list): List of arguments.
            **kwargs (dict): Dictionary of keyword arguments.

        Returns:
            None
        """

        # Initialize the parent mixin class
        super().__init__(app=app, *args, **kwargs)

        # Set the app and register it with the extension
        self._register_app(app)

        # set the logger
        logger.verbosity_level = self.get_config("API_VERBOSITY_LEVEL", 0)

        # initialize the api spec
        # Initialize the api spec
        self.api_spec = None

        if self.get_config("FULL_AUTO", True):
            self.init_api(app=app, **kwargs)
        if self.get_config("API_CREATE_DOCS", True):
            self.init_apispec(app=app, **kwargs)

        # create the rate limiter, it needs to always created as rate limits can be per model and doesn't have to
        # be global, so we dont know if it needs to be used in advance.
        logger.log(2, "Creating rate limiter")
        storage_uri = check_services()

        self.app.config["RATELIMIT_HEADERS_ENABLED"] = True
        self.app.config["RATELIMIT_SWALLOW_ERRORS"] = True
        self.app.config["RATELIMIT_IN_MEMORY_FALLBACK_ENABLED"] = True  #
        self.limiter = Limiter(app=app, key_func=get_remote_address, storage_uri=storage_uri if storage_uri else None)

    def _register_app(self, app: Flask):
        """
                Registers the app with the extension, and saves it to self.

        Args:
            app (Flask): The flask app.

        Returns:
            None

        """
        if FLASK_APP_NAME not in app.extensions:
            app.extensions[FLASK_APP_NAME] = self

        self.app = app

    def init_apispec(self, app: Flask, **kwargs):
        """
                Initializes the api spec object.


        Args:
            app (Flask): The flask app.
            **kwargs (dict): Dictionary of keyword arguments.

        Returns:
            None

        """

        # Initialize the api spec object

        # Create the api spec object, which is a subclass of APISpec. That subclass is defined above.
        self.api_spec = CurrySpec(app=app, naan=self, **kwargs)

    def init_api(self, **kwargs):
        """
                Initializes the api object, which handles flask route creation for models.


        Args:
            **kwargs (dict): Dictionary of keyword arguments.

        Returns:
            None

        """

        # Initialize the api object

        # Create the api spec object, which is a subclass of APISpec. That subclass is defined above.
        self.api = RiceAPI(naan=self, **kwargs)

    def to_api_spec(self):
        """

        Returns the api spec object.

        Returns:
            APISpec: The api spec json object.

        """
        if self.api_spec:
            return self.api_spec.to_dict()

    def get_config(self, key, default: Optional = None):
        """
                Gets a config value from the app config.

        Args:
            key (str): The key of the config value.
            default (Optional): The default value to return if the key is not found.

        Returns:
            Any : The config value.

        """
        if self.app:
            return self.app.config.get(key, default)

    def scheema_constructor(
            self,
            output_schema: Optional[Type[Schema]] = None,
            input_schema: Optional[Type[Schema]] = None,
            model: Optional[DeclarativeBase] = None,
            group_tag: Optional[str] = None,
            many: Optional[Callable] = None,
            **kwargs
    ) -> Callable:
        """
        Decorator to specify OpenAPI metadata for an endpoint, along with schema information for the input and output.
        If supplied, it also handles`

        Args:
            output_schema (Optional[Type[Schema]], optional): Output schema. Defaults to None.
            input_schema (Optional[Type[Schema]], optional): Input schema. Defaults to None.
            model (Optional[DeclarativeBase], optional): Database model. Defaults to None.
            group_tag (Optional[str], optional): Group name. Defaults to None.
            many (Optional[Callable], optional): Handler function. Defaults to None.
            kwargs (dict): Dictionary of keyword arguments.

        Returns:
            Callable: The decorated function.

        """

        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapped(*_args, **_kwargs):

                f_decorated = f

                # Deal with the authentication method
                auth_method = get_config_or_model_meta("API_AUTHENTICATE", model=model, output_schema=output_schema, input_schema=input_schema, default=False)
                if auth_method == "jwt":
                    f_decorated = None #authentication(f_decorated)
                elif auth_method == "basic":
                    f_decorated = None #authentication(f_decorated)
                elif auth_method == "api_key":
                    f_decorated = None #authentication(f_decorated)

                # deal with the output
                f_decorated = handle_many(output_schema, input_schema)(f_decorated) if many else handle_one(output_schema, input_schema)(f_decorated)

                # Check if rate limiting is to be applied
                rl = get_config_or_model_meta("API_RATE_LIMIT", model=model, input_schema=input_schema, output_schema=output_schema, default=False)
                if rl and isinstance(rl, str) and validate_flask_limiter_rate_limit_string(rl):
                    # Apply rate limiting
                    f_decorated = self.limiter.limit(rl)(f_decorated)
                elif rl:
                    # Apply global rate limiting
                    rule = get_rule(self, f).rule
                    logger.error(f"Rate limit definition not a string or not valid. Skipping for `{rule}` route.")

                # return output
                result = f_decorated(*_args, **_kwargs)
                return result

            route_info = {
                "function": wrapped,
                "output_schema": output_schema,
                "input_schema": input_schema,
                "model": model,
                "group_tag": group_tag,
                "many_to_many_model": kwargs.get("many_to_many_model"),
                "multiple": many or kwargs.get("multiple"),
                "parent": kwargs.get("parent_model"),
            }

            self.set_route(route_info)

            return wrapped

        return decorator

    @classmethod
    def get_templates_path(cls):
        """
        Gets the path to the templates folder.
        Returns:
            str: The path to the templates folder.
        """
        spec = importlib.util.find_spec(cls.__module__)
        source_dir = os.path.split(spec.origin)[0]
        return os.path.join(source_dir, "html")

    def set_route(self, route: dict):
        """
        Adds a route to the route spec list, which is used to generate the api spec.

        Args:
            route (dict): The route object.

        """

        # this needs to be here due to the way that the routes are inspected. The api_spec object is not available
        # at the time of route inspection

        # add to the decorator object if it doesn't exist
        if not hasattr(route["function"], "_decorators"):
            route["function"]._decorators = []

        # Add the api_spec decorator to the function
        route["function"]._decorators.append(self.scheema_constructor)

        self.route_spec.append(route)
