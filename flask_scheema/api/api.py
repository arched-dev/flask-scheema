import os
import secrets
import time
from types import FunctionType
from typing import Optional, Callable, Union, List, Any, Dict

from flask import current_app, Blueprint, g
from sqlalchemy.orm import Session
from werkzeug.exceptions import default_exceptions

from flask_scheema.api.auth import auth_required
from flask_scheema.api.decorators import (
    handle_many,
    handle_one
)
from flask_scheema.api.exception_handling import handle_http_exception
from flask_scheema.api.utils import (
    get_description,
    setup_route_function,
    get_tag_group,
    endpoint_namer,
    get_models_relationships, get_primary_keys,
)
from flask_scheema.extensions import logger
from flask_scheema.scheema.bases import AutoScheema, DeleteSchema
from flask_scheema.scheema.utils import (
    get_input_output_from_model_or_make,
)
from flask_scheema.services.database import CrudService
from flask_scheema.utilities import (
    AttributeInitializerMixin,
    get_config_or_model_meta,
)


class RiceAPI(AttributeInitializerMixin):
    created_routes: dict = {}
    naan: "Naan"
    api_full_auto: Optional[bool] = True
    api_base_model: Optional[Callable] = None
    api_base_schema: Optional[Callable] = AutoScheema
    db_service: Optional[Callable] = CrudService
    session: Optional[Union[Session, List[Session]]] = None
    blueprint: Optional[Blueprint] = None

    def __init__(self, naan: "Naan", *args, **kwargs):
        """
        Initializes the RiceAPI object.

        Args:
            naan (Naan): The naan object.
            *args (list): List of arguments.
            **kwargs (dict): Dictionary of keyword arguments.

        """

        super().__init__(*args, **kwargs)
        self.naan = naan
        if self.api_full_auto:
            self.validate()
            self.register_blueprint_and_error_handler()
            self.create_routes()
            # flask blueprints to be registered after all routes are created
            self.naan.app.register_blueprint(self.blueprint)

    def validate(self):
        """
        Validates the RiceAPI object.
        """
        if self.api_full_auto:
            if not self.api_base_model:
                raise ValueError(
                    "If FULL_AUTO is True, API_BASE_MODEL must be set to a SQLAlchemy model."
                )

            if not isinstance(self.api_base_model, list):
                self.api_base_model = [self.api_base_model]

            # check that the base model has a get_session function.
            for base in self.api_base_model:
                if not hasattr(base, "get_session"):
                    raise ValueError(
                        "If FULL_AUTO is True, API_BASE_MODEL must have a `get_session` function that returns"
                        "the database session for that model."
                    )

            if not current_app.config.get("FLASK_SECRET_KEY") and not current_app.config.get("SECRET_KEY"):
                raise ValueError(
                    "SECRET_KEY must be set in the Flask app config. You can use this randomly generated key:\n"
                    f"{secrets.token_urlsafe(24)}\n"
                    f"And this SALT key\n"
                    f"{secrets.token_urlsafe(16)}\n"
                )

            user = get_config_or_model_meta("API_USER_MODEL", default=None)
            auth = get_config_or_model_meta("API_AUTHENTICATE")
            if not user and auth and callable(auth):
                raise ValueError(
                    "If API_AUTHENTICATE is set to a callable, API_USER_MODEL must be set to the user model."
                )

            if auth and callable(auth) and not hasattr(user, "email") and (not hasattr(user, "password") and not hasattr(user, "api_key")):
                raise ValueError(
                    "The user model must have an email and password or api_key field if a authentication function is set."
                )

    def create_routes(self):
        """
        Creates all the routes for the api.
        """

        for base in self.api_base_model:
            for model_class in base.__subclasses__():
                if hasattr(model_class, "__table__"):
                    session = model_class.get_session()
                    self.make_all_model_routes(model_class, session)

    def register_blueprint_and_error_handler(self):
        """
        Register custom error handler for all http exceptions.
        Returns:
            None
        """
        # Use Flask's error handler to handle default HTTP exceptions
        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api")
        self.blueprint = Blueprint('api', __name__, url_prefix=api_prefix)

        for code in default_exceptions.keys():
            logger.debug(4, f"Setting up custom error handler for blueprint |{self.blueprint.name}| with http code +{code}+.")
            self.blueprint.register_error_handler(code, handle_http_exception)

        @self.blueprint.before_request
        def before_request(*args, **kwargs):
            g.start_time = time.time()

    def make_all_model_routes(self, model: Callable, session: Any):
        """
        Creates all the routes for a given model.

        Args:
            model (Callable): The model to create routes for.
            session (Any): The database session to use for the model.

        Returns:
            None

        """

        # Get blocked methods from Meta class, if any
        blocked_methods = []
        if hasattr(model, "Meta") and hasattr(model.Meta, "block"):
            blocked_methods = model.Meta.block_methods
            logger.debug(4, f"Blocked methods for -{model.__name__}- are +{blocked_methods}+. Skipping these methods.")

        for _method in ["GETS", "GET", "POST", "PUT", "DELETE"]:
            # Skip generating routes for methods in blocklist
            if _method in blocked_methods:
                continue

            kwargs = self._prepare_route_data(model, session, _method)
            self.generate_route(**kwargs)

        # Sets up a secondary route for relations that is accessible from just the `foreign_key`
        relations = get_models_relationships(model)
        for relation_data in relations:
            relation_data = self._prepare_relation_route_data(relation_data, session)
            self._create_relation_route_and_to_url_function(relation_data)

    def _create_relation_route_and_to_url_function(self, relation_data: Dict):
        """
        Creates a route for a relation and adds a to_url function to the model.

        Args:
            relation_data:

        Returns:

        """
        child = relation_data["child_model"]
        parent = relation_data["parent_model"]
        self._add_relation_url_function_to_model(
            child=child, parent=parent, id_key=relation_data["join_key"]
        )
        self.generate_route(**relation_data)

    def _prepare_route_data(
        self, model: Callable, session: Any, http_method: str
    ) -> Dict[str, Any]:
        """
        Prepares the data for a route.

        Args:
            model (Callable): The model to create routes for.
            session (Any): The database session to use for the model.
            http_method (str): The HTTP method for the route.

        Returns:
            dict: The route data.

        """

        is_multiple = http_method == "GETS"

        input_schema_class, output_schema_class = get_input_output_from_model_or_make(
            model
        )

        url_naming_function = get_config_or_model_meta(
            "endpoint_namer", model, default=endpoint_namer
        )

        base_url = (
            f"/{url_naming_function(model, input_schema_class, output_schema_class)}"
        )

        method = "GET" if is_multiple else http_method
        logger.debug(4, f"Collecting main model data for -{model.__name__}- with expected url |{method}|:`{base_url}`.")

        return {
            "model": model,
            "handler": handle_many if is_multiple else handle_one,
            "method": method,
            "url": base_url,
            "name": model.__name__.lower(),
            "output_schema": output_schema_class,
            "authentication": get_config_or_model_meta("API_AUTHENTICATE", model=model, default=False),
            "session": session,
            "multiple": is_multiple,
            "input_schema": input_schema_class
            if http_method in ["POST", "PUT"]
            else None,
        }

    def _prepare_relation_route_data(
        self, relation_data: Dict, session: Any
    ) -> Dict[str, Any]:
        """
        Prepares the data for a relation route.

        Args:
            relation_data (Callable): The model to create routes for.
            session (Any): The database session to use for the model.

        Returns:
            dict: The route data.

        """
        child_model = relation_data["model"]
        parent_model = relation_data["parent"]
        is_multiple = relation_data["is_multiple"]

        input_schema_class, output_schema_class = get_input_output_from_model_or_make(
            child_model
        )
        pinput_schema_class, poutput_schema_class = get_input_output_from_model_or_make(
            parent_model
        )

        url_naming_function = get_config_or_model_meta(
            "endpoint_namer", child_model, default=endpoint_namer
        )

        parent_model_pk = get_primary_keys(parent_model).key

        relation_url = f"/{url_naming_function(parent_model, pinput_schema_class, poutput_schema_class)}/<{parent_model_pk}>/{url_naming_function(child_model, input_schema_class, output_schema_class)}"

        logger.debug(4, f"Collecting parent/child model relationship for -{parent_model.__name__}- and -{child_model.__name__}- with expected url `{relation_url}`.")

        return {
            "child_model": child_model,
            "model": child_model,
            "parent_model": parent_model,
            "handler": handle_many if is_multiple else handle_one,
            "multiple": relation_data["join_type"][-4:].lower() == "many",
            "method": "GET",
            "relation_name": relation_data["relationship"],
            "url": relation_url,
            "name": child_model.__name__.lower()
            + "_join_to_"
            + parent_model.__name__.lower(),
            "join_key": relation_data["right_column"],
            "output_schema": output_schema_class,
            "authentication": get_config_or_model_meta("API_AUTHENTICATE", model=child_model, default=False),
            "session": session,
        }

    def _add_to_created_routes(self, **kwargs):
        """
        Adds a route to the created routes' dictionary.


        Args:
            **kwargs (dict): dictionary of keyword args

        Returns:
            None

        """
        if kwargs["name"] not in self.created_routes:
            self.created_routes[kwargs["name"]] = kwargs

        model = kwargs.get("child_model", kwargs.get("model"))
        self.created_routes[kwargs["name"]] = {
            "function": kwargs["name"],
            "model": model,
            "name": kwargs["name"],
            "method": kwargs["method"],
            "url": kwargs["url"],
            "input_schema": kwargs.get("input_schema"),
            "output_schema": kwargs.get("output_schema"),
            "authentication": get_config_or_model_meta("API_AUTHENTICATE", model=model, default=False),
        }

    def generate_route(self, **kwargs: dict):
        """
        Generated the route for this method/model. It pulls various information from the model's Meta class, if it
        exists.

        Args:
            **kwargs (dict): dictionary of keyword args

        Returns:
            None

        """
        # Get the description from the Meta class, if it exists for redoc
        description = get_description(kwargs)

        # this is for redoc to group the routes
        tag_group: str = get_tag_group(kwargs)
        if tag_group:
            kwargs["group_tag"] = tag_group

        # Get the model and session for the Service
        model = kwargs.get("model", kwargs.get("child_model"))
        service = CrudService(model=model, session=kwargs["session"])

        # Get the http method from the kwargs or default to GET
        http_method: str = kwargs.get("method", "GET")

        # Get the route function
        route_function = setup_route_function(
            service,
            http_method,
            multiple=kwargs.get("multiple", False),
            join_model=kwargs.get("parent_model", None),
            get_field=kwargs.get("join_key"),
        )

        # create the actual route function and add it to flask
        if kwargs["method"] in ["GETS", "GET", "DELETE", "PUT"] and not kwargs.get(
            "multiple", False
        ) and not kwargs.get("relation_name"):
            kwargs["url"] += "/<id>"

        if kwargs["method"] == "DELETE":
            kwargs["output_schema"] = DeleteSchema

        def route_function_template(*args, **kwargs):
            return route_function(*args, **kwargs)   #*args, *list(kwargs.values()),

        route_function_template.__doc__ = "---\n" + description

        unique_function_name = (
            f"route_wrapper_{http_method}_{kwargs['url'].replace('/', '_')}"
        )
        unique_route_function = FunctionType(
            route_function_template.__code__,
            globals(),
            unique_function_name,
            route_function_template.__defaults__,
            route_function_template.__closure__,
        )
        kwargs["function"] = unique_route_function

        logger.debug(4, f"Creating route function ${unique_function_name}$ for model -{model.__name__}-")

        # Add the route to flask and wrap in the decorator.
        self._add_route_to_flask(
            kwargs["url"],
            kwargs["method"],
            self.naan.scheema_constructor(**kwargs)(unique_route_function),
        )

        # Add the to_url method to the model
        not kwargs.get("join_key") and self._add_self_url_function_to_model(model)
        # Add the route to the created routes dictionary
        self._add_to_created_routes(**kwargs)

    def _add_route_to_flask(self, url: str, method: str, function: Callable):
        """
        Adds a route to flask

        Args:
            url (str): The url endpoint
            method (str): The HTTP method
            function (Callable): The function to call when the route is visited

        Returns:
            None

        """

        logger.log(1, f"|{method}|:`{self.blueprint.url_prefix}{url}` added to flask.")
        self.blueprint.add_url_rule(url, view_func=function, methods=[method])

    def _add_self_url_function_to_model(self, model: Callable):
        """
                Adds a method to the model class

        Args:
            model (Callable): The model to add the function to

        Returns:
            None

        """
        # Get the primary keys
        primary_keys = [key.name for key in model.__table__.primary_key]

        # Check for composite primary keys
        if len(primary_keys) > 1:
            logger.error(f"Composite primary keys are not supported, failed to set method $to_url$ on -{model.__name__}-")
            return

        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api")

        url_naming_function = get_config_or_model_meta(
            "endpoint_namer", model, default=endpoint_namer
        )

        def to_url(self):
            return f"{api_prefix}/{url_naming_function(model)}/{getattr(self, primary_keys[0])}"

        logger.log(3,f"Adding method $to_url$ to model -{model.__name__}-")
        setattr(model, "to_url", to_url)

    def _add_relation_url_function_to_model(
        self, id_key: str, child: Callable, parent: Callable
    ):
        """
        Adds a method to the model class

        Args:
            model (Callable): The model to add the function to.

        Returns:
            None

        """
        # Get the primary keys
        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api")

        parent_endpoint = get_config_or_model_meta(
            "endpoint_namer", parent, default=endpoint_namer
        )(parent)

        child_endpoint = get_config_or_model_meta(
            "endpoint_namer", child, default=endpoint_namer
        )(child)
        child_endpoint_function_name = child_endpoint.replace("-", "_")

        parent_pk = get_primary_keys(parent).key
        def to_url(self):
            return f"{api_prefix}/{parent_endpoint}/{getattr(self,parent_pk)}/{child_endpoint_function_name}"

        logger.log(3,f"Adding relation method ${child_endpoint_function_name}_to_url$ to parent model -{parent.__name__}- linking to -{child.__name__}-.")
        setattr(parent, child_endpoint_function_name + "_to_url", to_url)