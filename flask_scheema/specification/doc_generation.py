import copy
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Callable

import pytz
from apispec import APISpec
from flask import current_app
from marshmallow import Schema
from marshmallow_sqlalchemy.fields import RelatedList, Related
from sqlalchemy.orm import DeclarativeBase
from werkzeug.routing import IntegerConverter, UnicodeConverter

from flask_scheema.services.operators import aggregate_funcs

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
html_path = ""


def make_endpoint_description(schema: Schema, http_method: str, **kwargs):
    """
        Generates endpoint description from a schema for the API docs.

        Only applicable in FULL_AUTO mode or if AUTO_NAME_ENDPOINTS = True


    Args:
            schema (Callable): Schema to generate endpoint description from.
            http_method (str): HTTP method.

        Returns:
            str: Endpoint description.

    """
    many = kwargs.get("multiple")
    name = (
        kwargs.get("model").__name__ if kwargs.get("model") else schema.__name__
    ).replace("Schema", "")

    parent = kwargs.get("parent")

    if http_method == "GET" and parent and many:
        return f"Returns a list of `{name}` for a specific `{parent.__name__}`"
    elif http_method == "GET" and parent and not many:
        return f"Get a `{name}` by id for a specific `{parent.__name__}`."
    elif http_method == "GET" and many:
        return f"Returns a list of `{name}`"
    elif http_method == "GET" and not many:
        return f"Get a `{name}` by id."
    elif http_method == "POST":
        return f"Create a new `{name}`."
    elif http_method == "PUT":
        return f"Update an existing `{name}`."
    elif http_method == "PATCH":
        return f"Update an existing `{name}`."
    elif http_method == "DELETE":
        return f"Delete a `{name}`."
    else:
        return "Endpoint description not available"


def generate_fields_description(schema: "AutoScheema") -> str:
    """
        Generates fields description from a schema for the API docs.

    Args:
            schema (AutoScheema): Schema to generate fields description from.

        Returns:
            str: Fields description.

    """
    from flask_scheema.utilities import (
        manual_render_absolute_template,
    )

    fields = [
        (k, v.metadata.get("description", ""))
        for k, v in schema().fields.items()
        if v
           and v.dump_only in [None, False]
           and not isinstance(v, RelatedList)
           and not isinstance(v, Related)
    ]

    if hasattr(schema, "Meta") and hasattr(schema.Meta, "model"):
        table_name = schema.Meta.model.__name__
        example_table = (
            "OtherTable.name,OtherTable.age,OtherTable.id,OtherTable.email"
        ).split(",")

        def get_table_name(x):
            temp_fields = copy.deepcopy([x[0] for x in fields])
            random.shuffle(temp_fields)
            if x == 0:
                current_fields = temp_fields[:3]
            elif x == 1:
                current_fields = [table_name + "." + x for x in temp_fields[:3]]
            else:
                current_fields = []
                for _ in range(5):
                    table_choices = random.choice([table_name, "OtherTable"])
                    if table_choices == table_name:
                        current_table_and_field = (
                                table_name + "." + random.choice(temp_fields)
                        )
                    else:
                        current_table_and_field = random.choice(example_table)
                    current_fields.append(current_table_and_field)

            return "fields=" + ",".join(current_fields)

        example_fields = [get_table_name(x) for x in range(3)]

        full_path = os.path.join(html_path, "redoc_templates/fields.html")

        from flask_scheema.utilities import get_config_or_model_meta
        from flask_scheema.api.utils import endpoint_namer
        schema_name = get_config_or_model_meta("API_ENDPOINT_NAMER", schema.Meta.model, default=endpoint_namer)(
            schema.Meta.model)
        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api")

        return manual_render_absolute_template(
            full_path, schema_name=schema_name, api_prefix=api_prefix, fields=fields, example_fields=example_fields
        )

    return "None"


def generate_x_description(template_data: Dict, path: str = "") -> str:
    """
        Generates filter examples from a model, e.g.:
        Filters to apply on the data. E.g. id=1, name=John, age>20. Supported operators: =, >, <, like, in.#


    Args:
            template_data (dict): Template data to generate filter examples from.
            path (str): Path to the template.

        Returns:
            str: Filter examples.

    """

    from flask_scheema.utilities import (
        manual_render_absolute_template,
    )

    if template_data:
        full_path = os.path.join(html_path, path)
        return manual_render_absolute_template(full_path, **template_data)
    else:
        return "This endpoint does not have a database table (or is computed etc) and should not be filtered\n"


def generate_filter_examples(schema: Callable) -> str:
    """
        Generates filter examples from a model, e.g.:
        Filters to apply on the data. E.g. id=1, name=John, age>20. Supported operators: =, >, <, like, in.#


    Args:
            schema (AutoScheema): Schema to generate filter examples from.

        Returns:
            str: Filter examples.

    """

    from flask_scheema.utilities import (
        manual_render_absolute_template,
    )

    now: datetime = datetime.now(pytz.utc)
    yesterday: datetime = datetime.now(pytz.utc) - timedelta(days=1)
    operators = {
        "Integer": [
            "__eq",
            "__lt",
            "__le",
            "__gt",
            "__ge",
            "__ne",
            "__in",
            "__nin",
            "__like",
            "__ilike",
        ],
        "Float": [
            "__eq",
            "__lt",
            "__le",
            "__gt",
            "__ge",
            "__ne",
            "__in",
            "__nin",
            "__like",
            "__ilike",
        ],
        "String": ["__eq", "__ne", "__in", "__nin", "__like", "__ilike"],
        "Bool": ["__eq", "__ne", "__in", "__nin"],
        "Date": ["__eq", "__lt", "__le", "__gt", "__ge", "__ne", "__in", "__nin"],
        "DateTime": ["__eq", "__lt", "__le", "__gt", "__ge", "__ne", "__in", "__nin"],
        "Time": ["__eq", "__lt", "__le", "__gt", "__ge", "__ne", "__in", "__nin"],
    }
    day_before_yesterday: datetime = yesterday - timedelta(days=1)

    examples = []

    example_values = {
        "Integer": ["1", "10", "100", "500", "1000"],
        "Float": ["1.25", "2.50", "3.75", "5.00"],
        "String": ["John", "Doe", "Jane"],
        "Boolean": ["true", "false"],
        "Date": [
            now.date().strftime(DATE_FORMAT),
            yesterday.date().strftime(DATE_FORMAT),
            day_before_yesterday.date().strftime(DATE_FORMAT),
        ],
        "DateTime": [
            now.strftime(DATETIME_FORMAT),
            yesterday.strftime("%Y-%m-%d %H:%M:%S"),
            day_before_yesterday.strftime("%Y-%m-%d %H:%M:%S"),
        ],
        "Time": ["12:00:00", "13:00:00", "14:00:00"],
    }

    fields = schema().fields
    columns = [k for k, v in fields.items() if v and v.dump_only in [None, False]]

    for column in columns:
        col_type = type(fields[column]).__name__
        if col_type in operators:
            chosen_operator = random.choice(operators[col_type])
            if chosen_operator in ["__in", "__nin"]:
                chosen_values = ", ".join(
                    [
                        random.choice(example_values.get(col_type, ["value"]))
                        for _ in range(3)
                    ]
                )
                chosen_value = f"({chosen_values})"
                examples.append(f"{column}{chosen_operator}={chosen_value}")
            else:
                chosen_value = random.choice(example_values.get(col_type, ["value"]))
                examples.append(f"{column}{chosen_operator}={chosen_value}")

    split_examples = int(len(examples) / 3)
    example_one = "&".join(examples[:split_examples])
    example_two = "&".join(examples[-split_examples:])

    full_path = os.path.join(html_path, "redoc_templates/filters.html")

    return manual_render_absolute_template(
        full_path, examples=[example_one, example_two]
    )


def get_template_data_for_model(schema) -> Optional[dict]:
    """
        Generates model data for jinja template and redoc.

    Args:
            schema (AutoScheema): Schema to generate model data for.

        Returns:
            dict: Model data.
    """

    from flask_scheema.utilities import extract_sqlalchemy_columns
    from flask_scheema.utilities import extract_relationships
    from flask_scheema.utilities import get_config_or_model_meta
    from flask_scheema.api.utils import table_namer

    table_namer = get_config_or_model_meta("API_TABLE_NAMER", default=table_namer)

    if hasattr(schema, "Meta") and hasattr(schema.Meta, "model"):
        base_model = schema.Meta.model
        base_table = table_namer(base_model)
        base_columns = extract_sqlalchemy_columns(base_model)

        model_relationships = extract_relationships(base_model)
        model_relationship_names = [table_namer(x) for x in model_relationships]

        if isinstance(model_relationships, list) and len(model_relationships) > 0:
            relationship_columns = extract_sqlalchemy_columns(model_relationships[0])
            relationship_table = table_namer(model_relationships[0])
        else:
            relationship_columns = []
            relationship_table = None

        aggs = ", ".join([f"`{x}`" for x in list(aggregate_funcs.keys())])

        template_data = {
            "relationship_table": relationship_table,
            "relationship_columns": relationship_columns,
            "base_table": base_table,
            "base_columns": base_columns,
            "aggs": aggs,
            "model_relationship_names": model_relationship_names,
        }
        return template_data


def generate_path_params_from_rule(model, rule) -> List[dict]:
    """
    Generates path parameters from a Flask routing rule.

    Args:
        model (DeclarativeBase): Model to generate path parameters from.
        rule (Rule): Rule to generate path parameters from.

    Returns:
        List[dict]: List of path parameters with enhanced type checks and descriptions.
    """
    path_params = []
    for argument in rule.arguments:
        # Initialize param_info with common properties
        param_info = {
            "name": argument,
            "in": "path",
            "required": True,
            "description": f"Identifier for the {model.__name__} instance."
        }

        # Assign type based on the converter used in the rule
        converter = rule._converters[argument]
        if isinstance(converter, IntegerConverter):
            param_info["schema"] = {"type": "integer"}
            param_info["description"] += " This is an integer value uniquely identifying the object."
        elif isinstance(converter, UnicodeConverter):
            param_info["schema"] = {"type": "string"}
            param_info["description"] += " This is a string identifier for the object."
        else:
            # Fallback for other converter types, customize as needed
            param_info["schema"] = {"type": "string"}
            param_info["description"] += " Unique identifier for the object."

        path_params.append(param_info)
    return path_params


def generate_query_params_from_rule(rule, methods, schema, many) -> List[dict]:
    """
        Generates path parameters from a rule.


    Args:
        rule (Rule): Rule to generate path parameters from.
        methods (set): Set of methods to generate query parameters from.
        schema (Schema): Schema to generate query parameters from.
        many (bool): Whether the endpoint returns multiple items.

    Returns:
        List[dict]: List of path parameters.
    """
    from flask_scheema.utilities import get_config_or_model_meta
    query_params = []
    if "DELETE" in methods and get_config_or_model_meta("API_ALLOW_CASCADE_DELETE", getattr(schema.Meta, "model", None),
                                                        default=True):
        query_params.append({
            "name": "cascade_delete",
            "in": "query",
            "schema": {"type": "integer"},
            "description": (
                "Controls whether related entities should be deleted when the primary entity is deleted. "
                "Set to '1' to enable cascading delete, which will remove any associated entities in the database "
                "that are directly related to the entity being deleted. This action ensures that no orphaned "
                "records remain. "
                "Set to '0' to disable cascading delete, preventing the deletion of related entities. "
            )
        })
    if "GET" in methods and many:
        page_max = get_config_or_model_meta("API_PAGINATION_SIZE_MAX", default=100)
        page_default = get_config_or_model_meta("API_PAGINATION_SIZE_DEFAULT", default=20)
        query_params.append(
            {
                "name": "limit",
                "in": "query",
                "required": False,
                "schema": {"type": "integer"},
                "description": f"The maximum number of items to return in the response. Default `{page_default}` Maximum `{page_max}`.",
            }
        )
        query_params.append(
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer"},
                "description": "The pagination page number. Default `1`.",
            }
        )

    return query_params


def get_rule(naan, f):
    """
        Gets the path, methods and path parameters for a function.
    Args:
        schema (Schema): Schema to generate query parameters from.
        naan (Naan): The naan object.
        f (Callable): The function to get the path, methods and path parameters for.

    Returns:

    """
    for rule in naan.app.url_map.iter_rules():
        if rule.endpoint.split(".")[-1] == f.__name__:
            return rule

    return None


def register_routes_with_spec(naan: "Naan", route_spec: List):
    """
        Registers all flask_scheema with the apispec object.
        Which flask_scheema should be registered is determined by the decorators and builds the openapi spec, which is
        served with Redoc.


    Args:
            naan (Naan): The naan object.
            route_spec (List): List of routes/schemas to register with the apispec.

        Returns:
            None
    """

    from flask_scheema.scheema.bases import AutoScheema

    for route_info in route_spec:
        with naan.app.test_request_context():
            f = route_info["function"]

            # Get the correct endpoint and path using the function.

            from flask_scheema.utilities import (
                scrape_extra_info_from_spec_data,
            )

            rule = get_rule(naan, f)
            methods = rule.methods - {"OPTIONS", "HEAD"}

            for http_method in methods:

                route_info = scrape_extra_info_from_spec_data(
                    route_info, method=http_method, multiple=route_info.get("multiple", False)
                )

                path = rule.rule
                output_schema = route_info.get("output_schema")
                input_schema = route_info.get("input_schema")
                model = route_info.get("model")
                description = route_info.get("description")
                summary = route_info.get("summary")
                tag = route_info.get("tag")
                many = route_info.get("multiple")

                path_params = generate_path_params_from_rule(model, rule)
                query_params = generate_query_params_from_rule(rule, methods, output_schema, many)

                # We do not accept input schemas on GET or DELETE requests. They are handled with query parameters,
                # and not request bodies.
                if input_schema and http_method not in ["POST", "PATCH"]:
                    input_schema = None

                endpoint_spec = generate_swagger_spec(
                    http_method,
                    f,
                    output_schema=output_schema,
                    input_schema=input_schema,
                    model=model,
                    query_params=query_params,
                    path_params=path_params,
                    many=many
                )

                endpoint_spec["tags"] = [tag]


                # Add or update the tag group in the spec
                if route_info.get("group_tag"):
                    naan.api_spec.set_xtags_group(tag, route_info["group_tag"])

                # Split function docstring by '---' and set summary and description
                if summary:
                    endpoint_spec["summary"] = summary
                if description:
                    endpoint_spec["description"] = description

                naan.api_spec.path(
                    path=convert_path_to_openapi(path),
                    operations={http_method.lower(): endpoint_spec},
                )

    register_schemas(naan.api_spec, AutoScheema)


def convert_path_to_openapi(path: str) -> str:
    """
        Converts a flask path to an openapi path.


    Args:
            path (str): Flask path to convert.

        Returns:
            str: Openapi path.
    """
    return path.replace("<", "{").replace(">", "}").replace("<int:", "")


def register_schemas(
        spec: APISpec,
        input_schema: Schema,
        output_schema: Optional[Schema] = None,
        force_update=False,
):
    """
        Registers schemas with the apispec object.


    Args:
            spec (APISpec): APISpec object to register schemas with.
            input_schema (Schema): Input schema to register.
            output_schema (Schema): Output schema to register.
            force_update (bool): If True, will update the schema even if it already exists.
    """

    put_input_schema = None
    if input_schema:
        put_input_schema = copy.deepcopy(input_schema())
        put_input_schema.__name__ = f"patch_{input_schema.__name__}"
        for field_key, field in put_input_schema.fields.items():
            if field.required:
                put_input_schema.fields[field_key].required = False

    for schema in [input_schema, output_schema, put_input_schema]:
        if schema:
            schema_name = schema.__name__
            existing_schema = spec.components.schemas.get(schema_name)

            # Check if schema already exists
            if existing_schema:
                if force_update:
                    # Update the existing schema
                    spec.components.schemas[schema_name] = schema
                # else:
                #     print(f"Schema {schema_name} already exists. Skipping.")
            else:
                # Add the new schema
                spec.components.schema(schema_name, schema=schema)


def initialize_spec_template(method, many=False, rate_limit=False):
    """
    Initializes the spec template with optional rate limiting headers for successful and rate-limited responses.

    Args:
        method: The HTTP method.
        many: Whether the endpoint returns multiple items.
        rate_limit: Whether the endpoint has a rate limit.

    Returns:
        dict: Spec template.
    """
    from flask_scheema.utilities import get_config_or_model_meta

    # Base responses applicable to all endpoints
    responses = {
        "200": {
            "description": "Successful operation",
        },
        "500": {
            "description": "Internal server error"
        }
    }

    # Adjust for non-POST methods when not returning multiple items
    if method != "POST" and not many:
        responses["404"] = {"description": "Resource not found"}

    # Authentication and permission responses based on configuration
    if get_config_or_model_meta("API_AUTHENTICATE", default=False):
        responses.setdefault("401", {"description": ""})
        responses["401"]["description"] += " You need to be authenticated to access this resource."
        responses.setdefault("403", {"description": ""})
        responses["403"]["description"] += " You do not have the required permissions to access this resource."

    # Define rate limit headers
    rate_limit_headers = {
        "X-RateLimit-Limit": {
            "type" : "integer",
            "description": "The maximum number of requests allowed in a time window.",
            "example": 100
        },
        "X-RateLimit-Remaining": {
            "type": "integer",
            "description": "The number of requests remaining in the current rate limit window.",
            "example": 99  # Default example for successful responses
        },
        "X-RateLimit-Reset": {
            "type": "integer",
            "description": "The time at which the current rate limit window resets (in UTC epoch seconds).",
            "example": 15830457
        },
        "Retry-After": {
            "type": "integer",
            "description": "The amount of time to wait before making another request (in seconds).",
            "example": 20
        }
    }

    # If rate limiting is enabled, adjust for 429 response
    if rate_limit:
        responses["429"] = {
            "description": "Too many requests. You have exceeded the rate limit.",
            "headers": rate_limit_headers.copy()
        }
        responses["429"]["headers"]["X-RateLimit-Remaining"]["example"] = 0  # Adjust for 429 response

        # Apply rate limit headers to successful response
        responses["200"].setdefault("headers", {}).update(rate_limit_headers)

    return {
        "responses": responses,
        "parameters": [],
    }

def append_parameters(
        spec_template: Dict,
        query_params: List[Dict],
        path_params: List[Dict],
        http_method: str,
        input_schema: Schema = None,
        output_schema: Schema = None,
        model: DeclarativeBase = None,
        many: bool = False,
):
    """
    Enhances a spec template with parameters, request bodies, and responses for API documentation.

    Args:
        spec_template (Dict): The OpenAPI specification template to enhance.
        query_params (List[Dict]): A list of dictionaries defining query parameters.
        path_params (List[Dict]): A list of dictionaries defining path parameters.
        http_method (str): The HTTP method (GET, POST, PUT, DELETE, PATCH).
        input_schema (Schema, optional): The Marshmallow schema for request body validation.
        output_schema (Schema, optional): The Marshmallow schema for response data serialization.
        model (DeclarativeBase, optional): The SQLAlchemy model for database interactions.
        many (bool, optional): Whether the endpoint returns multiple items.

    Returns:
        None: Modifies the spec_template in-place.
    """
    from flask_scheema.utilities import get_config_or_model_meta

    global html_path
    html_path = current_app.extensions["flask_scheema"].get_templates_path()

    # Ensure 'parameters' key exists in spec_template
    spec_template.setdefault("parameters", [])

    if not query_params:
        query_params = []
    if not path_params:
        path_params = []

    # Append path and query parameters
    spec_template["parameters"].extend(path_params + query_params)

    rl = get_config_or_model_meta("API_RATE_LIMIT", model=model, input_schema=input_schema, output_schema=output_schema, default=False)
    if rl:
        description = spec_template.get("description", "")
        description += f"\n**Rate Limited** - requests on this endpoint are limited to `{rl}`." if rl else ""
        spec_template["description"] = description

    # Handle requestBody for methods expecting a payload
    if http_method in ["POST", "PATCH"] and input_schema:
        # PUT and PATCH methods do not necessarily require all fields
        spec_template["requestBody"] = {
            "description": f"`{input_schema.__name__.replace('Schema', '')}` payload.",
            "required": http_method == "POST",  # Only POST requests require the entire payload
            "content": {
                "application/json": {
                    # PATCH requests do not necessarily require all fields, so I have defined a separate schema for it
                    # which has all fields as optional
                    "schema": {
                        "$ref": f"#/components/schemas/{'patch_' if http_method == 'PATCH' else ''}{input_schema.__name__}"}
                }
            },
        }

    # Add a generic 200 response based on output_schema, if available
    if output_schema:
        spec_template.setdefault("responses", {})  # Ensure 'responses' key exists
        spec_template["responses"]["200"].update({
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{output_schema.__name__}"}
                }
            },
        })

    # Handling for GET and DELETE operations
    if http_method in ["GET"] and model and many:
        spec_template["parameters"].extend(
            [
                {
                    "name": "filters",
                    "in": "query",
                    "schema": {"type": "string"},
                    "description": generate_filter_examples(output_schema),  #
                },
            ]
        )

        template_data = get_template_data_for_model(output_schema)
        spec_template["parameters"].extend(
            make_endpoint_params_description(output_schema, template_data)
        )

    add_auth_to_spec(model, spec_template)


def add_auth_to_spec(model, spec_template: Dict):
    from flask_scheema.utilities import get_config_or_model_meta
    auth_on = get_config_or_model_meta("API_AUTHENTICATE", model=model, default=False)
    auth_type = get_config_or_model_meta("API_AUTHENTICATE_METHOD", model=model, default=None)
    if auth_on and auth_type == "basic":
        # Ensure there's a section for security requirements
        spec_template.setdefault("security", [])
        spec_template["security"].append({"basicAuth": []})  # This refers to the security scheme defined globally

        # Ensure the global components object exists and add the Basic Auth security scheme if not already present
        spec_template.setdefault("components", {})
        spec_template["components"].setdefault("securitySchemes", {})
        spec_template["components"]["securitySchemes"]["basicAuth"] = {
            "type": "http",
            "scheme": "basic",
            "description": (
                "Basic Authentication. Credentials must be provided as a Base64-encoded string "
                "in the format `username:password` in the `Authorization` header."
            )
        }
    elif auth_on and auth_type == "jwt":
        # Ensure there's a section for security requirements
        spec_template.setdefault("security", [])
        spec_template["security"].append({"bearerAuth": []})  # This refers to the security scheme defined globally

        # Ensure the global components object exists and add the JWT Bearer Auth security scheme if not already present
        spec_template.setdefault("components", {})
        spec_template["components"].setdefault("securitySchemes", {})
        spec_template["components"]["securitySchemes"]["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",  # Indicates a JWT is expected
            "description": "JWT Authentication. A valid JWT must be sent in the `Authorization` header as `Bearer <token>`."
        }
    elif auth_on and auth_type == "api_key":
        # Define where the API key should be sent; let's assume "header" for this example
        api_key_location = "header"  # Other common value is "query"
        api_key_name = "X-API-KEY"  # Name of the header or query parameter

        spec_template.setdefault("security", [])
        spec_template["security"].append({"apiKeyAuth": []})  # This refers to the security scheme defined globally

        spec_template.setdefault("components", {})
        spec_template["components"].setdefault("securitySchemes", {})
        spec_template["components"]["securitySchemes"]["apiKeyAuth"] = {
            "type": "apiKey",
            "in": api_key_location,  # Can be "header" or "query"
            "name": api_key_name,  # Name of the header or query parameter to be used
            "description": f"API Key Authentication. An API key must be sent in the `{api_key_name}` {api_key_location}."
        }


def make_endpoint_params_description(schema: Schema, data: dict):
    """
        Generates endpoint parameters description from a schema for the API docs.


    Args:
            schema (Schema): Schema to generate endpoint parameters description from.
            data (dict): Data to generate endpoint parameters description from.

        Returns:
            List[dict]: Endpoint parameters description.

    """
    from flask_scheema.utilities import get_config_or_model_meta

    output = []

    if get_config_or_model_meta("API_ALLOW_SELECT_FIELDS", getattr(schema.Meta, "model", None), default=True):
        output.append(
            {
                "name": "fields",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_fields_description(schema),
            }
        )

    if get_config_or_model_meta("API_ALLOW_ORDERBY", getattr(schema.Meta, "model", None), default=True):
        output.append(
            {
                "name": "order by",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_x_description(
                    data, "redoc_templates/order.html"
                ),
            }
        )
    if get_config_or_model_meta("API_ALLOW_JOIN", getattr(schema.Meta, "model", None), default=True):
        output.append(
            {
                "name": "joins",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_x_description(
                    data, "redoc_templates/joins.html"
                ),
            }
        )
    if get_config_or_model_meta("API_ALLOW_GROUPBY", getattr(schema.Meta, "model", None), default=True):
        output.append(
            {
                "name": "group by",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_x_description(
                    data, "redoc_templates/group.html"
                ),
            }
        )
    if get_config_or_model_meta("API_ALLOW_AGGREGATION", getattr(schema.Meta, "model", None), default=True):
        output.append(
            {
                "name": "aggregation",
                "in": "query",
                "schema": {"type": "string"},
                "description": generate_x_description(
                    data, "redoc_templates/aggregate.html"
                ),
            }
        )
    return output


def handle_authorization(f, spec_template):
    roles_required = None
    if hasattr(f, "_decorators"):
        for decorator in f._decorators:
            if decorator.__name__ == "auth_required":
                roles_required = decorator._args
                spec_template["parameters"].append(
                    {
                        "name": "Authorization",
                        "in": "header",
                        "description": "JWT token required",
                        "required": True,
                        "schema": {"type": "string"},
                        "format": "jwt",
                    }
                )
                break

    if roles_required:
        roles_desc = ", ".join(roles_required)
        spec_template["responses"]["401"][
            "description"
        ] += f" Roles required: {roles_desc}."


def generate_swagger_spec(
        http_method: str,
        f: Callable,
        input_schema: Schema = None,
        output_schema: Schema = None,
        model: DeclarativeBase = None,
        query_params: list = None,
        path_params: list = None,
        many: bool = False,
) -> dict:
    spec = current_app.extensions["flask_scheema"].api_spec

    # Register Schemas
    register_schemas(spec, input_schema, output_schema)

    from flask_scheema.utilities import get_config_or_model_meta
    rl = get_config_or_model_meta("API_RATE_LIMIT", model=model, output_schema=output_schema, input_schema=input_schema, default=False)
    # Initialize spec template
    spec_template = initialize_spec_template(http_method, many, rl)

    # Append parameters to spec_template
    append_parameters(
        spec_template, query_params, path_params, http_method, input_schema, output_schema, model, many
    )

    # Handle Authorization in the documentation
    handle_authorization(f, spec_template)

    return spec_template
