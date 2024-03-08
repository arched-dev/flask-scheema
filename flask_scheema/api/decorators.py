from functools import wraps
from typing import Optional, List
from typing import Type, Callable, Any, Dict, Union

from flask import request
from marshmallow import Schema
from sqlalchemy.exc import ProgrammingError
from werkzeug.exceptions import HTTPException

from flask_scheema.api.responses import (
    deserialize_data,
    serialize_output_with_mallow,
    create_response,
    CustomResponse,
)
from flask_scheema.api.utils import list_model_columns, convert_case
from flask_scheema.exceptions import CustomHTTPException
from flask_scheema.scheema.bases import AutoScheema
from flask_scheema.utilities import get_config_or_model_meta

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403


def handle_many(output_schema: Type[AutoScheema], input_schema=None) -> Callable:
    """
    A decorator to handle multiple records from a route.

    Args:
        output_schema (Schema): The Marshmallow schema to serialize the output.

    Returns:
        Callable: The decorated function.
    """

    def decorator(func: Callable) -> Callable:
        """
        Decorator to handle input and output using Marshmallow schemas for multiple record operations.

        Args:
            func (Callable): The function to be decorated.

        Returns:
            Callable: The decorated function.

        """

        @wraps(func)
        @standardize_response
        @fields(output_schema, many=True)
        def wrapper(
            *args: Any, **kwargs: Dict[str, Any]
        ) -> Union[Dict[str, Any], tuple]:
            """Inner wrapper function that gets executed when decorated function is called."""

            # Getting the output schema from the decorator
            new_output_schema: Optional[Type[AutoScheema]] = kwargs.pop("schema", None)

            # Getting the query from kwargs
            result = func(*args, **kwargs)

            # Serializing the output
            if new_output_schema:
                model = new_output_schema.Meta.model

                model_columns = list_model_columns(
                    model
                )  # todo check whats happening here!! Why is this here?
                schema_columns = list_schema_fields(new_output_schema)

                return check_serialise_method_and_return(
                    result,
                    model_columns=model_columns,
                    schema_columns=schema_columns,
                    schema=new_output_schema,
                )

            return result

        return wrapper

    return decorator


def handle_one(
    output_schema: Type[AutoScheema], input_schema: Optional[Type[AutoScheema]] = None
) -> Callable:
    """
    Decorator to handle input and output using Marshmallow schemas for single record operations.

    Args:
        output_schema (Schema, optional): The Marshmallow schema to serialize output.
        input_schema (Schema, optional): The Marshmallow schema to validate and deserialize input.

    Returns:
        Callable: The decorated function.

    Examples:
        @app.route('/addresses/<int:address_id>', methods=['GET'])
        @authrequired([])
        @handle_one(AddressSchema, AddressSchema)
            def get_address(address_id: int, deserialized_data: Dict[str, Any]) -> Dict[str, Any]:
                return Address.query.get(address_id)

    """

    # set the input schema to the output schema if not provided

    def decorator(func: Callable) -> Callable:
        """
        Decorator to handle input and output using Marshmallow schemas for single record operations.

        Args:
            func (Callable): The function to be decorated.

        Returns:
            Callable: The decorated function.

        """

        @wraps(func)
        @standardize_response
        @fields(output_schema, many=False)
        def wrapper(
            *args: Any, **kwargs: Dict[str, Any]
        ) -> Union[Dict[str, Any], tuple]:
            """Inner wrapper function that gets executed when decorated function is called."""

            # Deserializing and validating input if input_schema is provided

            # Deserializing and validating input if input_schema is provided
            if input_schema:
                data_or_error = deserialize_data(input_schema, request.json)
                if isinstance(data_or_error, tuple):  # This means there was an error
                    case = get_config_or_model_meta("API_FIELD_CASE", "snake")
                    error = {convert_case(k, case): v for k, v in data_or_error[0].items()}
                    raise CustomHTTPException(
                        400, error
                    )
                kwargs["deserialized_data"] = data_or_error
                kwargs["model"] = input_schema.Meta.model

            new_output_schema: Optional[Type[AutoScheema]] = kwargs.pop("schema", None)

            result = func(*args, **kwargs)
            if new_output_schema:
                return serialize_output_with_mallow(new_output_schema, result)

            return result

        return wrapper

    return decorator


def get_count(result, value):
    # Check if value is a list, a single item, or None, and adjust count accordingly
    if result.get("total_count", None):
        return result.get("total_count")
    elif isinstance(value, list):
        return len(value)
    elif value is None:
        return 0
    else:
        return 1


def handle_error(e: Any, status_code):
    """
        Handle errors and return a standardised response.

    Args:
        e (Exception): The exception.
        status_code (int): The status code to return.

    Returns:
        response: an error response
    """
    error_func = get_config_or_model_meta(
        key="API_ERROR_CALLBACK", method=request.method
    )
    if error_func:
        import traceback

        error_func(e, traceback)

    return create_response(error=str(e), status=status_code)


def handle_result(result):
    status_code = HTTP_OK
    count = 1
    value = result
    next_url = None
    previous_url = None

    if isinstance(result, tuple):
        status_code = (
            result[1] if len(result) == 2 and isinstance(result[1], int) else HTTP_OK
        )
        result = result[0]

    if isinstance(result, dict):
        value = result.get("query", result)
        count = get_count(result, value)
        next_url = result.get("next_url")
        previous_url = result.get("previous_url")
    if isinstance(result, CustomResponse):
        next_url = result.next_url
        previous_url = result.previous_url

    return status_code, value, count, next_url, previous_url


def standardize_response(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print_exc = get_config_or_model_meta(key="API_PRINT_EXCEPTIONS", default=True)
        error_func = get_config_or_model_meta(
            key="API_ERROR_CALLBACK", method=request.method
        )

        def print_exc_run_error(e):
            """
            Print the exception and the stack trace.

            Args:
                e: The exception to print.

            Returns:
                None
            """
            import traceback

            if error_func:
                error_func(e, traceback)

            if print_exc:
                print(e)
                traceback.print_exc()

        try:
            result = f(*args, **kwargs)
            status_code, value, count, next_url, previous_url = handle_result(result)
            error = None if status_code < HTTP_BAD_REQUEST else value
            return create_response(
                value=value if not error else None,
                errors=error,
                status=status_code,
                count=count,
                next_url=next_url,
                previous_url=previous_url,
            )

        except HTTPException as e:
            print_exc_run_error(e)
            return create_response(
                status=e.code, errors=[{"error": e.name, "reason": e.description}]
            )
        except ProgrammingError as e:
            print_exc_run_error(e)
            text = str(e).split(")")[1].split("\n")[0].strip().capitalize()
            return create_response(
                status=HTTP_BAD_REQUEST,
                errors=[{"error": "SQL Format Error", "reason": text}],
            )
        except CustomHTTPException as e:
            print_exc_run_error(e)
            return create_response(
                status=e.status_code,
                errors=[
                    {
                        "error": e.error,
                        "reason": (
                            e.reason if isinstance(e.reason, dict) else str(e.reason)
                        ),
                    }
                ],
            )
        except Exception as e:
            print_exc_run_error(e)
            return create_response(
                status=HTTP_INTERNAL_SERVER_ERROR,
                errors=[{"error": "Internal Server Error", "reason": str(e)}],
            )

    return decorated_function


def fields(model_schema: Type[AutoScheema], many: bool = False) -> Callable:
    """
        A decorator to specify which fields to return in the response.


    Args:
        model_schema: Marshmallow schema for the model.
        many: Indicate whether to return multiple objects or a single object.

    Returns:
        Decorator function.


    Examples:
        /addresses?fields=id,account

        /addresses?fields=id,account,date_created

    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            This is the wrapper function, it will be called and preforms the following:
            1. Gets the fields from the request args
            2. If fields are specified, it will return only those fields
            3. If no fields are specified, it will return all fields



            Args:
                 **kwargs: key word args

            Returns:
                The function that was passed in, with the schema specified in the decorator

            """
            select_fields = request.args.get("fields")
            if select_fields and get_config_or_model_meta("API_ALLOW_SELECT_FIELDS", model_schema.get_model(), default=True):
                select_fields = select_fields.split(",")
                kwargs["schema"] = model_schema(many=many, only=select_fields)
            else:
                kwargs["schema"] = model_schema(many=many)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def list_schema_fields(schema: Schema):
    """
        Get all the fields from a schema

    Args:
        schema (Schema): The schema to get the fields from

    Returns:
        Dict: A dictionary of all the fields

    """

    return list(schema.fields.keys())


def check_serialise_method_and_return(
    result: Dict, schema: AutoScheema, model_columns: List, schema_columns: List
):
    """
        Checks to see if the columns that have been output match the columns in the model and schema, if not its likely a
        custom serialise method has been used, and we should return the result as is (list of dicts) rather than serialising
        in marshmallow.


    Args:
        result (Dict): The result dictionary
        schema (Schema): The schema to get the fields from
        model_columns (List): The model columns
        schema_columns (List): The schema columns


    Returns:
        Dict: A dictionary of all the fields
    """
    from flask_scheema.api.responses import serialize_output_with_mallow

    output_list = result.pop("dictionary", list())
    mallow_serialise = True
    if len(output_list) > 0:
        output_keys = list(output_list[0].keys())
        missing_model_columns = len([x for x in output_keys if x not in model_columns])
        missing_schema_columns = len(
            [x for x in output_keys if x not in schema_columns]
        )
        if missing_model_columns > 0 or missing_schema_columns > 0:
            mallow_serialise = False

    return (
        serialize_output_with_mallow(schema, result)
        if mallow_serialise
        else output_list
    )
