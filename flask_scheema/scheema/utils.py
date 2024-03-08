import re
from types import new_class
from typing import Optional, Callable

from marshmallow import fields
from marshmallow_sqlalchemy.fields import Nested, Related, RelatedList

from flask_scheema.utilities import get_config_or_model_meta


def convert_snake_to_camel(snake_str):
    """
    Convert a snake_case string to camelCase, preserving a leading underscore if present.

    Args:
    - snake_str (str): The snake_case string to convert.

    Returns:
    - str: The converted camelCase string, with a leading underscore preserved if it was present.
    """
    # Check for a leading underscore and store this information
    leading_underscore = snake_str.startswith("_")

    # Split the string into components based on underscores
    components = snake_str.split("_")

    # If there was a leading underscore, the first component will be empty, so remove it
    if leading_underscore:
        components.pop(0)

    # Capitalize the first letter of each component except the first one,
    # join them together, and prepend an underscore if there was one originally
    return (
        ("_" if leading_underscore else "")
        + components[0]
        + "".join(x.title() for x in components[1:])
    )


def convert_camel_to_snake(camel_str):
    """
    Convert a camelCase string to snake_case.

    Args:
    - camel_str (str): The camelCase string to convert.

    Returns:
    - str: The converted snake_case string.
    """
    # Insert an underscore before any uppercase letters and convert the whole string to lowercase.
    snake_str = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", snake_str).lower()


def convert_kebab_to_snake(name: str) -> str:
    """
    Converts kebab case to snake case.
    """
    return name.replace("-", "_")


def get_scheema_subclass(model: callable, dump: Optional[bool] = False):
    """
        Searches through all subclasses of AutoScheema to find the one that matches the model and dump parameters.

    Args:
        model (callable): The model to search for.
        dump (bool): Whether to search for a dump or load schema.

    Returns:
        The subclass of AutoScheema that matches the model and dump parameters.
    """

    from flask_scheema.scheema.bases import AutoScheema

    schema_base = get_config_or_model_meta(
        "API_BASE_SCHEMA", model=model, default=AutoScheema
    )

    for subclass in schema_base.__subclasses__():
        schema_model = hasattr(subclass, "Meta") and getattr(
            subclass.Meta, "model", None
        )
        if schema_model == model and (
            getattr(subclass, "dump", False) is dump or getattr(subclass, "dump", None)
        ):
            return subclass
            # subclass is not type(self)


def create_dynamic_schema(base_class, model_class):
    """
        Creates a dynamic schema class that inherits from the base_class and has the model_class as its model.

    Args:
        base_class:
        model_class:

    Returns:

    """

    class Meta:
        model = model_class

    dynamic_class = new_class(
        f"{model_class.__name__}Schema",
        (base_class,),
        exec_body=lambda ns: ns.update(Meta=Meta),
    )
    return dynamic_class


def get_input_output_from_model_or_make(model: Callable):
    """
        Gets the input and output schemas from the model, or creates them if they do not exist.

    Args:
        model (Callable): The model to get the schemas from.

    Returns:
        tuple: The input and output schemas.

    """

    from flask_scheema.scheema.bases import AutoScheema

    # Generate input and output schema classes dynamically if they do not exist
    input_schema_class = get_scheema_subclass(model, dump=False)
    output_schema_class = get_scheema_subclass(model, dump=True)

    if input_schema_class is None:
        input_schema_class = create_dynamic_schema(AutoScheema, model)

    if output_schema_class is None:
        output_schema_class = create_dynamic_schema(AutoScheema, model)

    return input_schema_class, output_schema_class


type_mapping = {
    fields.String: "string",
    fields.Integer: "integer",
    fields.Float: "number",
    fields.Boolean: "boolean",
    fields.DateTime: "string",
    fields.Date: "string",
    fields.Time: "string",
    fields.UUID: "string",
    fields.URL: "string",
    fields.Function: "string",
    fields.Nested: "object",
    fields.Email: "string",
    fields.Dict: "object",
    fields.List: "array",
    Related: "object",
    RelatedList: "array",
}


def get_openapi_meta_data(field_obj):
    """
    Convert a marshmallow field to an OpenAPI type
    Args:
        field_obj:

    Returns:

    """
    openapi_type_info = {}
    field_type = type(field_obj)

    if (
        hasattr(field_obj, "parent")
        and hasattr(field_obj.parent, "Meta")
        and hasattr(field_obj.parent.Meta, "model")
    ):
        openapi_type_info = get_description_and_example_add(
            openapi_type_info, field_obj
        )

    # Handle basic types
    openapi_type = type_mapping.get(
        field_type, "string"
    )  # Default to 'string' if type not found
    openapi_type_info["type"] = openapi_type

    # Handle DateTime, Date and Time formats
    if field_type in [fields.DateTime, fields.Date, fields.Time]:
        openapi_type_info["format"] = (
            "date-time"
            if field_type == fields.DateTime
            else field_type.__name__.lower()
        )
    if field_type in [fields.Function]:
        openapi_type_info["format"] = "url"
        openapi_type_info["example"] = "/url/to/resource"
    # Handle list types
    if field_type == fields.List:
        openapi_type_info["items"] = get_openapi_meta_data(field_obj.inner)

    # Handle nested fields (relationships)
    if field_type in [Nested, Related, RelatedList]:
        related_schema_name = None

        if field_type == Nested:
            related_schema_name = field_obj.schema.__class__.__name__
        elif field_type in [Related, RelatedList]:
            parent_model = (
                field_obj.parent.Meta.model
            )  # SQLAlchemy model from the parent schema
            related_model = getattr(
                parent_model, field_obj.name
            ).property.mapper.class_  # Related SQLAlchemy model
            related_schema_name = f"{related_model.__name__}Schema"  # Assuming schema names follow this convention

        if related_schema_name:
            if (
                hasattr(field_obj, "many") and field_obj.many
            ) or field_type == RelatedList:
                openapi_type_info["type"] = "array"
                openapi_type_info["items"] = {
                    "$ref": f"#/components/schemas/{related_schema_name}"
                }
            else:
                openapi_type_info["$ref"] = (
                    f"#/components/schemas/{related_schema_name}"
                )

    return openapi_type_info


def get_description_and_example_add(openapi_type_info, field_obj):
    """
    Get the description from the model field and add it to the openapi_type_info dict
    Args:
        openapi_type_info:
        field_obj:

    Returns:

    """

    if hasattr(field_obj.parent.Meta.model, field_obj.name):
        model_field = getattr(field_obj.parent.Meta.model, field_obj.name)
        if hasattr(model_field, "info"):
            model_field_metadata = model_field.info

            if model_field_metadata.get("description"):
                desc = model_field_metadata.get("description")
                if desc:
                    openapi_type_info["description"] = desc

            if model_field_metadata.get("example"):
                example = model_field_metadata.get("example")
                if example:
                    openapi_type_info["example"] = example

    return openapi_type_info
