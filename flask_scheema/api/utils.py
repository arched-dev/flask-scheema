from typing import Optional, Callable

from flask import abort, request
from marshmallow import Schema
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

from flask_scheema.logging import logger
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
            "endpoint_namer", parent, default=endpoint_namer
        )
        return f"Get multiple `{name}` records from the database based on the parent {url_naming_function(parent)} id"

    if hasattr(model, "Meta") and hasattr(model.Meta, "description"):
        method_description = model.Meta.description.get(method)
        if method_description:
            return method_description

    # Fallback to default descriptions
    return {
        "DELETE": f"Delete a single `{name}` in the database by its id",
        "PUT": f"Put (update) a single `{name}` in the database.",
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

    def pre_process(pre_hook, **kwargs):
        if pre_hook:
            pre_hook(model=service.model, **kwargs)

    def post_process(post_hook, output):
        if post_hook:
            return post_hook(model=service.model, output=output)
        return output

    def route_function_factory(action, pre_hook=None, post_hook=None, **kwargs):
        def route_function(id=None, **kwargs):
            pre_process(pre_hook, args=request.args.to_dict(), id=id, get_field=get_field, join_model=join_model,
                        multiple=multiple)
            action_kwargs = {'lookup_val': id} if id else {}
            action_kwargs.update(kwargs)
            output = action(**action_kwargs) or abort(404)
            return post_process(post_hook, output)

        return route_function

    pre_hook = get_config_or_model_meta(f"API_PRE_{method}", model=service.model, default=None)
    post_hook = get_config_or_model_meta(f"API_POST_{method}", model=service.model, default=None)

    if method == "GET":
        action = lambda **kwargs: service.get_query(request.args.to_dict(), alt_field=get_field, multiple=multiple,
                                                    **kwargs)
    elif method == "DELETE":
        action = service.delete
    elif method == "PUT":
        action = lambda **kwargs: service.update(**kwargs)
    elif method == "POST":
        action = lambda **kwargs: service.create(**kwargs)

    return route_function_factory(action, pre_hook, post_hook)

# def setup_route_function(
#     service,
#     method,
#     multiple=False,
#     join_model: Optional[Callable] = None,
#     get_field: Optional[str] = None,
# ):
#     """
#     Sets up the route function for the API, based on the method. Returns a function that can be used as a route.
#
#     Args:
#         service (CrudService): The CRUD service for the model.
#         method (str): The HTTP method.
#         multiple (bool): Whether the route is for multiple records or not.
#         join_model (Callable): The model to use in the join.
#         get_field (str): The field to get the record by.
#
#     Returns:
#         function: The route function.
#     """
#     if method == "GET":
#
#         pre_get = get_config_or_model_meta("API_PRE_GET", model=service.model, default=None)
#         post_get = get_config_or_model_meta("API_POST_GET", model=service.model, default=None)
#
#         if get_field and not join_model:
#             def get_route_function(id):
#                 if pre_get:
#                     pre_get(model=service.model, args=request.args.to_dict(), id=id, get_field=get_field, join_model=join_model, multiple=multiple)
#                 out = service.get_query(request.args.to_dict(), alt_field=get_field, lookup_val=id, multiple=multiple) or abort(404)
#                 if post_get:
#                     out = post_get(model=service.model, output=out)
#                 return out
#             return get_route_function
#
#         if get_field and join_model:
#             def get_join_route_function(id):
#                 if pre_get:
#                     pre_get(model=service.model, args=request.args.to_dict(), id=id, get_field=get_field, join_model=join_model,
#                             multiple=multiple)
#                 out = service.get_query(request.args.to_dict(), alt_field=get_field, lookup_val=id, multiple=multiple, other_model=join_model) or abort(404)
#                 if post_get:
#                     out = post_get(model=service.model, output=out)
#                 return out
#             return get_join_route_function
#
#         if multiple:
#             def get_multiple_route_function():
#                 if pre_get:
#                     pre_get(model=service.model, args=request.args.to_dict(), multiple=multiple)
#                 out = service.get_query(request.args.to_dict(), multiple=multiple)
#                 if post_get:
#                     out = post_get(model=service.model, output=out)
#                 return out
#             return get_multiple_route_function
#
#         def get_single_route_function(id):
#             if pre_get:
#                 pre_get(model=service.model, args=request.args.to_dict(), id=id, multiple=multiple)
#             out = service.get_query(request.args.to_dict(), lookup_val=id, multiple=multiple) or abort(404)
#             if post_get:
#                 out = post_get(model=service.model, output=out)
#             return out
#
#         return get_single_route_function
#
#     elif method == "DELETE":
#         def delete_route_function(id):
#             pre_delete = get_config_or_model_meta("API_PRE_DELETE", model=service.model, default=None)
#             post_delete = get_config_or_model_meta("API_POST_DELETE", model=service.model, default=None)
#
#             if pre_delete:
#                 pre_delete(model=service.model, args=request.args.to_dict(), id=id)
#
#             out =  service.delete(id) or abort(404)
#
#             if post_delete:
#                 out = post_delete(model=service.model, output=out)
#
#             return out
#
#         return delete_route_function
#
#     elif method == "PUT":
#         def put_route_function():
#             pre_put = get_config_or_model_meta("API_PRE_PUT", model=service.model, default=None)
#             post_put= get_config_or_model_meta("API_POST_PUT", model=service.model, default=None)
#
#             if pre_put:
#                 pre_put(model=service.model, args=request.args.to_dict(), json=request.json)
#
#             out = service.update(request.json) or abort(404)
#
#             if post_put:
#                 out = post_put(model=service.model, output=out)
#
#             return out
#         return put_route_function
#
#     elif method == "POST":
#         def post_route_function():
#             pre_post = get_config_or_model_meta("API_PRE_POST", model=service.model, default=None)
#             post_post = get_config_or_model_meta("API_POST_POST", model=service.model, default=None)
#
#             if pre_post:
#                 pre_post(model=service.model, args=request.args.to_dict(), json=request.json)
#
#             out = service.create(request.json)
#
#             if post_post:
#                 out = post_post(model=service.model, output=out)
#
#             return out
#
#         return post_route_function


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

    kebab_name = camel_to_kebab(model.__name__)
    if kebab_name.endswith("s"):
        return kebab_name
    elif kebab_name.endswith("y"):
        return kebab_name[:-1] + "ies"
    else:
        return kebab_name + "s"


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
