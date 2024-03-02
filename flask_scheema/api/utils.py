from typing import Optional, Callable

from flask import abort, request
from marshmallow import Schema
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

from flask_scheema.logging import logger
from flask_scheema.services.operators import get_all_columns_and_hybrids
from flask_scheema.utilities import get_config_or_model_meta


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
        "GET": f"Get a single `{name}` in the database by its id"
        if not kwargs.get("multiple", False)
        else f"Get multiple `{name}` records from the database",
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


def setup_route_function(service, method, multiple=False, join_model: Optional[Callable] = None,
                         get_field: Optional[str] = None):
    """
    Sets up the route function for the API, based on the method. Returns a function that can be used as a route.

    Args:
        service (CrudService): The CRUD service for the model.
        method (str): The HTTP method.
        multiple (bool): Whether the route is for multiple records or not.
        join_model (Callable): The model to use in the join.
        get_field (str): The field to get the record by.

    Returns:
        function: The route function.
    """

    def post_process(post_hook, output, id=id, field=get_field, join_model=join_model, **kwargs):
        if post_hook:
            return post_hook(model=service.model, output=output)
        return output

    def route_function_factory(action, post_hook=None, **kwargs):
        def route_function(id=None, **kwargs):

            action_kwargs = {'lookup_val': id} if id else {}
            action_kwargs.update(kwargs)
            output = action(**action_kwargs) or abort(404)
            return post_process(post_hook, output, id=id, field=get_field, join_model=join_model, **kwargs)

        return route_function


    post_hook = get_config_or_model_meta(f"API_CALLBACK", model=service.model, default=None, method=method)

    if method == "GET":
        action = lambda **kwargs: service.get_query(request.args.to_dict(), alt_field=get_field, multiple=multiple,
                                                    **kwargs)
    elif method == "DELETE":
        action = service.delete
    elif method == "PUT" or method == "PATCH":
        action = lambda **kwargs: service.update(**kwargs)
    elif method == "POST":
        action = lambda **kwargs: service.create(**kwargs)

    return route_function_factory(action, post_hook)


def table_namer(model: Optional[DeclarativeBase] = None) -> str:
    """
    Gets the table name from the model name by converting camel case and kebab-case to snake_case.
    Args:
        model (DeclarativeBase): The model to get the table name for.

    Returns:
        str: The table name in snake_case.
    """
    from flask_scheema.scheema.utils import convert_camel_to_snake, convert_kebab_to_snake

    if model is None:
        return ""
    model_name = model.__name__
    # First convert kebab-case to snake_case
    snake_case_name = convert_kebab_to_snake(model_name)
    # Then convert camelCase to snake_case
    snake_case_name = convert_camel_to_snake(snake_case_name)
    return snake_case_name

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

    def camel_to_kebab(s):
        result = [s[0].lower()]
        for char in s[1:]:
            if char.isupper():
                result.extend(["-", char.lower()])
            else:
                result.extend([char])
        return "".join(result)

    kebab_name = camel_to_kebab(model.__name__).replace("_", "-")
    if kebab_name.endswith("s"):
        return kebab_name
    elif kebab_name.endswith("y"):
        return kebab_name[:-1] + "ies"
    else:
        return kebab_name + "s"


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
    elif parent_model_pk.type.python_type == float:
        pk_key = f"<float:{pk_key}>"
    elif parent_model_pk.type.python_type == bool:
        pk_key = f"<bool:{pk_key}>"
    elif parent_model_pk.type.python_type == list:
        pk_key = f"<list:{pk_key}>"
    elif parent_model_pk.type.python_type == dict:
        pk_key = f"<dict:{pk_key}>"
    elif parent_model_pk.type.python_type == set:
        pk_key = f"<set:{pk_key}>"
    elif parent_model_pk.type.python_type == tuple:
        pk_key = f"<tuple:{pk_key}>"
    elif parent_model_pk.type.python_type == bytes:
        pk_key = f"<bytes:{pk_key}>"
    elif parent_model_pk.type.python_type == bytearray:
        pk_key = f"<bytearray:{pk_key}>"
    elif parent_model_pk.type.python_type == memoryview:
        pk_key = f"<memoryview:{pk_key}>"
    elif parent_model_pk.type.python_type == complex:
        pk_key = f"<complex:{pk_key}>"
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

        if rel.direction.name in ["MANYTOMANY", "ONETOMANY", "MANYTOONE"] or rel.uselist:
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
        logger.debug(4,
                     f"Relationship found for parent +{rel.parent.class_.__name__}+ "
                     f"and child +{rel.mapper.class_.__name__}+ "
                     f"joined on |{rel.direction.name}|:`{route_info['join_key']}`")
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
    from flask_scheema.api.utils import table_namer

    table_namer_func = get_config_or_model_meta(key="api_table_namer", model=model, default=table_namer)

    all_model_columns, _ = get_all_columns_and_hybrids(model, {})
    all_model_columns = all_model_columns.get(table_namer_func(model))

    try:
        return list(all_model_columns.keys())
    except:
        return all_model_columns
