import re
from typing import Optional, Callable

from flask import abort, request
from marshmallow import Schema
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

from flask_scheema.logging import logger
from flask_scheema.services.operators import get_all_columns_and_hybrids
from flask_scheema.utilities import get_config_or_model_meta
import inflect

p = inflect.engine()


def get_description(kwargs):
    """
    Gets the description for the route, first checking the model's Meta class for a description attribute,
    then if not found, returning a default description based on the method.

    kwargs:
        Keyword arguments that include the model and the method type (GET, POST, etc.)

    Returns:
        str: The description string for the route
    """
    name = kwargs["name"]
    method = kwargs["method"]
    model = kwargs.get("model", kwargs.get("child_model"))

    # custom child description
    if kwargs.get("child_model"):
        parent = kwargs.get("parent_model")
        url_naming_function = get_config_or_model_meta(
            "API_ENDPOINT_NAMER", parent, default=endpoint_namer
        )
        return f"Get multiple `{name}` records from the database based on the parent {url_naming_function(parent)} id"

    if hasattr(model, "Meta") and hasattr(model.Meta, "description"):
        method_description = model.Meta.description.get(method)
        if method_description:
            return method_description

    # Fallback to default descriptions
    return {
        "DELETE": f"Delete a single `{name}` in the database by its id",
        "PATCH": f"Patch (update) a single `{name}` in the database.",
        "POST": f"Post (create) a single `{name}` in the database.",
        "GET": (
            f"Get a single `{name}` in the database by its id"
            if not kwargs.get("multiple", False)
            else f"Get multiple `{name}` records from the database"
        ),
    }.get(method, "")


def get_tag_group(kwargs: dict) -> str:
    """
    Gets the x-tagGroup for the route, first checking the model's Meta class for a tag_group attribute,
    It is pulled from the group meta-attribute of the model.


    Args:
        kwargs: yword arguments that include the model and the method type (GET, POST, etc.)

    Returns:
        str: The description string for the route

    """
    model = kwargs.get("model", kwargs.get("child_model"))

    if hasattr(model, "Meta") and hasattr(model.Meta, "tag_group"):
        return model.Meta.tag_group


def setup_route_function(
    service,
    method,
    many,
    join_model: Optional[Callable] = None,
    get_field: Optional[str] = None,
    **kwargs,
):
    """
    Sets up the route function for the API, based on the method. Returns a function that can be used as a route.

    Args:
        service (CrudService): The CRUD service for the model.
        method (str): The HTTP method.
        many (bool): Whether the route is for multiple records or not.
        join_model (Callable): The model to use in the join.
        get_field (str): The field to get the record by.

    Returns:
        function: The route function.
    """

    def pre_process(pre_hook, **kwargs):
        if pre_hook:
            return pre_hook(
                model=service.model,
                **{k: v for k, v in kwargs.items() if k not in ["model"]},
            )
        return kwargs

    def post_process(post_hook, output, **kwargs):
        if post_hook:
            return post_hook(
                model=service.model,
                output=output,
                **{k: v for k, v in kwargs.items() if k not in ["output", "model"]},
            )
        kwargs.update({"output": output})
        return kwargs

    def route_function_factory(action, many, pre_hook=None, post_hook=None, **kwargs):
        def route_function(id=None, **kwargs):

            kwargs = pre_process(
                pre_hook=pre_hook,
                id=id,
                field=get_field,
                join_model=join_model,
                **kwargs,
            )

            action_kwargs = {"lookup_val": id} if id else {}
            action_kwargs.update(kwargs)
            output = action(many=many, **{k:v for k,v in action_kwargs.items() if k != "many"}) or abort(404)
            kwargs = post_process(
                post_hook=post_hook,
                output=output,
                id=id,
                field=get_field,
                join_model=join_model,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["post_hook", "output", "id", "field", "join_model"]
                },
            )
            return kwargs.get("output")

        return route_function

    pre_hook = get_config_or_model_meta(
        f"API_SETUP_CALLBACK", model=service.model, default=None, method=method
    )

    post_hook = get_config_or_model_meta(
        f"API_RETURN_CALLBACK", model=service.model, default=None, method=method
    )

    if method == "GET":
        action = lambda **kwargs: service.get_query(
            request.args.to_dict(), alt_field=get_field, **kwargs
        )
    elif method == "DELETE":
        action = service.delete
    elif method == "PUT" or method == "PATCH":
        action = lambda **kwargs: service.update(**kwargs)
    elif method == "POST":
        action = lambda **kwargs: service.create(**kwargs)

    return route_function_factory(action, many, pre_hook, post_hook, **kwargs)


def table_namer(model: Optional[DeclarativeBase] = None) -> str:
    """
    Gets the table name from the model name by converting camel case and kebab-case to snake_case.
    Args:
        model (DeclarativeBase): The model to get the table name for.

    Returns:
        str: The table name in snake_case.
    """
    from flask_scheema.scheema.utils import (
        convert_camel_to_snake,
        convert_kebab_to_snake,
    )

    if model is None:
        return ""
    model_name = model.__name__
    # First convert kebab-case to snake_case
    snake_case_name = convert_kebab_to_snake(model_name)
    # Then convert camelCase to snake_case
    snake_case_name = convert_camel_to_snake(snake_case_name)
    return snake_case_name


def convert_case(s, target_case):
    # Splitting the string into words considering various input cases
    if "_" in s:  # Handles snake_case and SCREAMING_SNAKE_CASE directly
        words = s.split("_")
    else:  # Handles camelCase and PascalCase
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", s)

    # Normalize words to lowercase for conversion
    words = [word.lower() for word in words]

    if target_case == "camel":
        return "".join(words[:1] + [word.capitalize() for word in words[1:]])
    elif target_case == "pascal":
        return "".join(word.capitalize() for word in words)
    elif target_case == "snake":
        return "_".join(words)
    elif target_case == "screaming_snake":
        return "_".join(word.upper() for word in words)
    elif target_case == "kebab":
        return "-".join(words)
    elif target_case == "screaming_kebab":
        return "-".join(word.upper() for word in words)
    else:
        # Return the original string if the target case is not recognized
        return s


def pluralize_last_word(converted_name):
    """
    Pluralize the last word of the converted name while preserving the rest of the name and its case.

    Args:
    - converted_name: The name after case conversion.

    Returns:
    - The name with the last word pluralized.
    """
    # Detecting the case from the converted name
    if "_" in converted_name:  # snake_case or SCREAMING_SNAKE_CASE
        words = converted_name.split("_")
        target_case = "snake" if words[0].islower() else "screaming_snake"
    elif "-" in converted_name:  # kebab-case or SCREAMING-KEBAB-CASE
        words = converted_name.split("-")
        target_case = "kebab" if words[0].islower() else "screaming_kebab"
    else:  # camelCase or PascalCase
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", converted_name)
        target_case = "camel" if converted_name[0].islower() else "pascal"

    # Pluralizing the last word
    last_word = words[-1]
    if p.singular_noun(last_word):
        # The word is plural, convert it to singular for accurate pluralization
        last_word_singular = p.singular_noun(last_word)
        last_word_pluralized = p.plural(last_word_singular)
    else:
        # The word is singular, pluralize directly
        last_word_pluralized = p.plural(last_word)

    # Replacing the last word with its plural form
    words[-1] = last_word_pluralized

    # Reconstructing the name based on the original case
    if target_case in ["snake", "screaming_snake"]:
        new_name = "_".join(words)
    elif target_case in ["kebab", "screaming_kebab"]:
        new_name = "-".join(words)
    elif target_case == "camel":
        new_name = "".join(words[:1] + [word.capitalize() for word in words[1:]])
    elif target_case == "pascal":
        new_name = "".join(word.capitalize() for word in words)
    else:
        # Return the original name if the target case is not recognized
        new_name = converted_name

    # Adjusting case for SCREAMING_SNAKE and SCREAMING-KEBAB
    if target_case == "screaming_snake":
        new_name = new_name.upper()
    elif target_case == "screaming_kebab":
        new_name = new_name.upper()

    return new_name


def endpoint_namer(
    model: Optional[DeclarativeBase] = None,
    input_schema: Optional[Schema] = None,
    output_schema: Optional[Schema] = None,
):
    """
    Gets the endpoint name for the model, based on the model name.

    Args:
        model (DeclarativeBase): The model to get the endpoint name for.
        input_schema (Schema): The input schema for the model.
        output_schema (Schema): The output schema for the model.

    Returns:
        str: The endpoint name.

    """

    case = get_config_or_model_meta(
        "API_ENDPOINT_CASE", default="kebab", model=model
    )
    converted_name = convert_case(model.__name__, case)

    return pluralize_last_word(converted_name)


def get_url_pk(model: DeclarativeBase):
    """
    Gets the primary key for the model, based on the model's primary key.

    Args:
        model (DeclarativeBase): The model to get the primary key for.

    Returns:
        str: The flask primary key for the model

    """
    parent_model_pk = get_primary_keys(model)
    pk_key = parent_model_pk.key
    if parent_model_pk.type.python_type == int:
        pk_key = f"<int:{pk_key}>"
    elif parent_model_pk.type.python_type == str:
        pk_key = f"<{pk_key}>"

    return pk_key


def get_models_relationships(model: Callable):
    """
    Checks the model for relations and returns a list of relations, if any.
    If the relation is a many to many, it will not log the association table as a relation but the other side of
    the relationship.

    Args:
        model (Callable): The model to check for relations

    Returns:
        list: A list of relations

    """
    if not model:
        return []

    mapper = inspect(model)
    relationships = []

    for rel in mapper.relationships:
        route_info = {
            "relationship": rel.key,
            "model": rel.mapper.class_,
            "parent": rel.parent.class_,
            "join_key": rel.primaryjoin,
            "manytomany": False,
        }

        if (
            rel.direction.name in ["MANYTOMANY", "ONETOMANY", "MANYTOONE"]
            or rel.uselist
        ):
            route_info["join_type"] = rel.direction.name
            route_info["is_multiple"] = True

            # Extract join columns
            join_condition = rel.primaryjoin
            if join_condition is not None:
                left_column = (
                    join_condition.left.name
                    if hasattr(join_condition.left, "name")
                    else None
                )
                right_column = (
                    join_condition.right.name
                    if hasattr(join_condition.right, "name")
                    else None
                )

                route_info["left_column"] = left_column
                route_info["right_column"] = right_column

            # Special handling for MANYTOMANY to get the "other side" of the relationship
            route_info["manytomany"] = rel.direction.name == "MANYTOMANY"
            relationships.append(route_info)
        logger.debug(
            4,
            f"Relationship found for parent +{rel.parent.class_.__name__}+ "
            f"and child +{rel.mapper.class_.__name__}+ "
            f"joined on |{rel.direction.name}|:`{route_info['join_key']}`",
        )
    return relationships


def get_primary_keys(model):
    """
    Gets the primary key columns for the model.

    Args:
        model (Callable): The model to get the primary key columns for.

    Returns:
        Column: The primary key column.

    """
    primary_key_columns = []
    mapper = inspect(model)
    for column in mapper.primary_key:
        primary_key_columns.append(column)
    return primary_key_columns[0]


def list_model_columns(model: "CustomBase"):
    """
        Get all columns and hybrids from a sqlalchemy model

    Args:
        model (CustomBase): The model to get the columns from

    Returns:
        List: A list of all the columns

    """

    from flask_scheema.utilities import get_config_or_model_meta
    from flask_scheema.api.utils import convert_case

    schema_case = get_config_or_model_meta(
        key="API_SCHEMA_CASE", model=model, default="camel"
    )

    all_model_columns, _ = get_all_columns_and_hybrids(model, {})
    all_model_columns = all_model_columns.get(convert_case(model.__name__, schema_case))

    return list(all_model_columns.keys())
