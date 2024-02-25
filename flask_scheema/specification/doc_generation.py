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
    many = schema().many
    name = (
        schema.Meta.model.__name__ if hasattr(schema.Meta, "model") else schema.__name__
    ).replace("Schema", "")

    parent = kwargs.get("parent")

    if http_method == "GET" and many:
        return f"Returns a list of `{name}` objects."
    elif http_method == "GET" and not many:
        return f"Returns a `{name}` object."
    elif http_method == "POST":
        return f"Creates a new `{name}` object."
    elif http_method == "PUT":
        return f"Updates a `{name}` object."
    elif http_method == "PATCH":
        return f"Updates a `{name}` object."
    elif http_method == "DELETE":
        return f"Deletes a `{name}` object."
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

    if hasattr(schema, "Meta") and hasattr(schema.Meta, "model"):
        base_model = schema.Meta.model
        base_table = base_model.__name__
        base_columns = extract_sqlalchemy_columns(base_model)

        model_relationships = extract_relationships(base_model)
        model_relationship_names = [x.__name__ for x in model_relationships]

        if isinstance(model_relationships, list) and len(model_relationships) > 0:
            relationship_columns = extract_sqlalchemy_columns(model_relationships[0])
            relationship_table = model_relationships[0].__name__
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


def generate_path_params_from_rule(rule) -> List[dict]:
    """
        Generates path parameters from a rule.


    Args:
            rule (Rule): Rule to generate path parameters from.

        Returns:
            List[dict]: List of path parameters.
    """
    path_params = []
    for argument in rule.arguments:
        param_info = {"name": argument, "in": "path", "required": True}
        if isinstance(rule._converters[argument], IntegerConverter):
            param_info["schema"] = {"type": "integer"}
        elif isinstance(rule._converters[argument], UnicodeConverter):
            param_info["schema"] = {"type": "integer"}
        else:
            param_info["schema"] = {"type": "integer"}
        path_params.append(param_info)
    return path_params


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
            for rule in naan.app.url_map.iter_rules():
                if rule.endpoint.split(".")[-1] == f.__name__:
                    path = rule.rule
                    methods = rule.methods - {"OPTIONS", "HEAD"}
                    path_params = generate_path_params_from_rule(rule)
                    break

            from flask_scheema.utilities import (
                scrape_extra_info_from_spec_data,
            )

            for http_method in methods:
                route_info = scrape_extra_info_from_spec_data(
                    route_info, method=http_method
                )

                output_schema = route_info.get("output_schema")
                input_schema = route_info.get("input_schema")
                model = route_info.get("model")
                description = route_info.get("description")
                summary = route_info.get("summary")
                tag = route_info.get("tag")

                # We do not accept input schemas on GET or DELETE requests. They are handled with query parameters,
                # and not request bodies.
                if input_schema and http_method not in ["POST", "PUT", "PATCH"]:
                    input_schema = None

                endpoint_spec = generate_swagger_spec(
                    http_method,
                    f,
                    output_schema=output_schema,
                    input_schema=input_schema,
                    model=model,
                    path_params=path_params,
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

    for schema in [input_schema, output_schema]:
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


def initialize_spec_template():
    """
    Initializes the spec template.
    Returns:
        dict: Spec template.
    """

    return {
        "responses": {
            "200": {"description": "Successful operation"},
            "401": {"description": "Unauthorized"},
            "403": {"description": "Forbidden"},
        },
        "parameters": [],
    }


def append_parameters(
        spec_template: dict,
        path_params: list,
        http_method: str,
        input_schema: Schema,
        output_schema: Schema,
        model: DeclarativeBase,
):
    """

        Appends parameters to the spec template based on the input.


    Args:
            spec_template (dict): Spec template to append parameters to.
            path_params (list): Path parameters to append.
            http_method (str): HTTP method to append parameters for.
            input_schema (Schema): Input schema to append.
            output_schema (Schema): Output schema to append.
            model (DeclarativeBase): Database model to append.

        Returns:
            None

    """
    global html_path
    html_path = current_app.extensions["flask_scheema"].get_templates_path()

    # Add 200 response based on the output_schema
    if output_schema:
        spec_template["responses"]["200"] = {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{output_schema.__name__}"}
                }
            },
        }

    if path_params:
        spec_template["parameters"].extend(path_params)

    if http_method in ["POST", "PUT", "PATCH"] and input_schema:
        spec_template["requestBody"] = {
            "description": f"{input_schema.__name__} payload"
                           + (
                               " (all fields are optional when updating records, but with out the id the model cannot be queries and "
                               "will therefor fail)"
                               if http_method == "PATCH"
                               else ""
                           ),
            "required": True if http_method == "POST" else False,
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{input_schema.__name__}"}
                }
            },
        }

    if http_method in ["DELETE", "GET"] and model:
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
        if http_method == "GET":
            # Add fields' parameter based on the output_schema
            template_data = get_template_data_for_model(output_schema)
            spec_template["parameters"].extend(
                make_endpoint_params_description(output_schema, template_data)
            )


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
        path_params: list = None,
) -> dict:
    spec = current_app.extensions["flask_scheema"].api_spec

    # Register Schemas
    register_schemas(spec, input_schema, output_schema)

    # Initialize spec template
    spec_template = initialize_spec_template()

    # Append parameters to spec_template
    append_parameters(
        spec_template, path_params, http_method, input_schema, output_schema, model
    )

    # Handle Authorization
    handle_authorization(f, spec_template)

    return spec_template
