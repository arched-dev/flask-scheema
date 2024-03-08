import inspect
import time
from datetime import datetime
from typing import Optional, Union, List, Any, Dict, Type, Tuple

import pytz
from flask import Response, current_app, jsonify, g
from marshmallow import Schema, ValidationError
from sqlalchemy.orm import DeclarativeBase

from flask_scheema.api.utils import convert_case
from flask_scheema.scheema.utils import convert_snake_to_camel
from flask_scheema.utilities import get_config_or_model_meta


class CustomResponse:
    """
    Custom response class to be used for serializing output.
    """

    def __init__(
        self,
        value: Optional[Union[List, Any]] = None,
        count: Optional[int] = 1,
        error: Optional[Union[List, Dict, Any]] = None,
        status_code: Optional[int] = 200,
        next_url: Optional[str] = None,
        previous_url: Optional[str] = None,
        many: Optional[bool] = False,
        response_ms: Optional[float] = None,
    ):
        self.response_ms = response_ms
        self.value = value
        self.count = count
        self.error = error
        self.status_code = status_code
        self.count = count
        self.next_url = next_url
        self.previous_url = previous_url
        self.many = many


def deserialize_data(
    input_schema: Type[Schema], data: Any
) -> Union[Dict[str, Any], Tuple[Dict[str, Any], int]]:
    """
        Utility function to deserialize data using a given Marshmallow schema.

    Args:
        input_schema (Type[Schema]): The Marshmallow schema to be used for deserialization.
        data (Any): The data to be deserialized.

    Returns:
        Union[Dict[str, Any], Tuple[Dict[str, Any], int]]: The deserialized data if successful, or a tuple containing
        errors and a status code if there's an error.
    """
    try:

        fields = [v.name for k, v in input_schema().fields.items() if not v.dump_only]
        data = {k: v for k, v in data.items() if k in fields}

        # if get_config_or_model_meta("API_CONVERT_TO_CAMEL_CASE", default=True):
        #     data = {convert_camel(k): v for k, v in data.items()}

        deserialized_data = input_schema().load(data=data, output_as_dict=True)

        return deserialized_data
    except ValidationError as err:
        return err.messages, 400


def filter_keys(model, schema: Type[Schema], data_dict_list: List[Dict]):
    # Extract column, property, and hybrid property names from the model
    inspector = inspect(model)
    model_keys = set([column.key for column in inspector.columns])
    model_properties = set(inspector.attrs.keys()).difference(model_keys)
    all_model_keys = model_keys.union(model_properties)

    # Get schema fields
    schema_fields = set(schema._declared_fields.keys())

    filtered_data = []
    for data_dict in data_dict_list:
        filtered_dict = {}
        for key, value in data_dict.items():
            if (
                key in all_model_keys
                or (key in schema_fields and schema._declared_fields[key].dump != False)
                or key not in all_model_keys
            ):
                filtered_dict[key] = value
        filtered_data.append(filtered_dict)
    return filtered_data


def dump_schema_if_exists(
    schema: Schema, data: Union[dict, DeclarativeBase], is_list=False
):
    """
    Serialize the data using the schema if the data exists.
    Args:
        schema (Schema): the schema to use for serialization
        data (Union[dict, DeclarativeBase]): the data to serialize
        is_list (bool): whether the data is a list

    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: the serialized data

    """
    if data:
        return schema.dump(data, many=is_list)
    return [] if is_list else None


def serialize_output_with_mallow(
    output_schema: Type[Schema],
    data: Any,
) -> CustomResponse:
    """
        Utility function to serialize output using a given Marshmallow schema.

    Args:
        output_schema (Type[Schema]): The Marshmallow schema to be used for serialization.
        data (Any): The data to be serialized.
    Returns:
        Union[Dict[str, Any], tuple]: The serialized data if successful, or a tuple containing errors and a status code if there's an error.
    """
    from flask_scheema.api.decorators import get_count

    try:
        is_list = (
            isinstance(data, list)
            or ("value" in data and isinstance(data["value"], list))
            or ("query" in data and isinstance(data["query"], list))
        )
        dump_data = data["query"] if "query" in data else data
        value = dump_schema_if_exists(output_schema, dump_data, is_list)
        # Check if value is a list, a single item, or None, and adjust count accordingly
        count = get_count(data, value)

        next_url = data.get("next_url", 1)
        previous_url = data.get("previous_url", 1)
        many = is_list

        response_ms = "n/a"
        # adds the response time if set in the config
        start = g.get("start_time", None)
        if start:
            response_ms = (time.time() - g.start_time) * 1000

        return CustomResponse(
            value=value,
            count=count,
            next_url=next_url,
            previous_url=previous_url,
            response_ms=response_ms,
            many=many,
        )

    except ValidationError as err:
        return CustomResponse(
            value=None, count=None, error=err.messages, status_code=500
        )


def create_response(
    value: Optional[Any] = None,
    status: int = 200,
    errors: Optional[Union[str, List]] = None,
    count: Optional[int] = 1,
    next_url: Optional[str] = None,
    previous_url: Optional[str] = None,
    response_ms: Optional[float] = None,
) -> Response:  # New parameter for count
    """
        Create a standardised response.

    Args:
        value (Optional): The value to be returned.
        status (Optional): HTTP status code.
        errors (Optional): Error message.
        count (Optional): Number of objects returned.
        next_url (Optional): URL for the next page of results.
        previous_url (Optional): URL for the previous page of results.
        response_ms (Optional): The time taken to generate the response.

    Returns:
        A standardised response dictionary.

    """

    # Check if value is a tuple containing both the value and a status code
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[1], int):
        status = value[1]  # Update the status code for the HTTP response
        value = value[0]  # Extract the value part of the tuple

    # Get current time with timezone
    current_time_with_tz = datetime.now(pytz.utc)

    # Convert it to ISO 8601 format (JavaScript-compatible)
    js_time_with_timezone = current_time_with_tz.isoformat()

    data = {
        "api_version": current_app.config.get("API_VERSION"),
        "datetime": js_time_with_timezone,
    }

    if isinstance(value, CustomResponse):
        status = int(value.status_code)
        errors = value.error
        count = value.count
        response_ms = value.response_ms
        next_url = value.next_url
        previous_url = value.previous_url
        value = value.value

    data.update(
        {
            "value": value,
            "status_code": int(str(status)),
            "errors": errors,
            "response_ms": response_ms,
            "total_count": count,  # Include the count key here
        }
    )

    if next_url or previous_url or count > 1 or isinstance(value, CustomResponse):
        data.update(
            {
                "next_url": next_url,
                "previous_url": previous_url,
            }
        )

    data = remove_values(data)

    field_case = get_config_or_model_meta("API_FIELD_CASE", default="snake_case")
    data = {convert_case(k, field_case): v for k, v in data.items()}

    response = jsonify(data)
    response.status_code = int(str(status))

    return response


def remove_values(data: dict) -> dict:
    """
    Remove values from the response based on the configuration settings.
    Args:
        data (dict): The response data.

    Returns:
        dict: The response data with the specified keys removed.
    """
    if "datetime" in data and not get_config_or_model_meta(
        "API_DUMP_DATETIME", default=True
    ):
        data.pop("datetime")
    if "api_version" in data and not get_config_or_model_meta(
        "API_DUMP_VERSION", default=True
    ):
        data.pop("api_version")
    if "status_code" in data and not get_config_or_model_meta(
        "API_DUMP_STATUS_CODE", default=True
    ):
        data.pop("status_code")
    if "response_ms" in data and not get_config_or_model_meta(
        "API_DUMP_RESPONSE_MS", default=True
    ):
        data.pop("response_ms")
    if "total_count" in data and not get_config_or_model_meta(
        "API_DUMP_TOTAL_COUNT", default=True
    ):
        data.pop("total_count")
    if (
        "next_url" in data
        and not get_config_or_model_meta("API_DUMP_NULL_NEXT_URL", default=True)
        and not data.get("next_url")
    ):
        data.pop("next_url")
    if (
        "previous_url" in data
        and not get_config_or_model_meta("API_DUMP_NULL_PREVIOUS_URL", default=True)
        and not data.get("previous_url")
    ):
        data.pop("previous_url")
    if (
        "errors" in data
        and not get_config_or_model_meta("API_DUMP_NULL_ERRORS", default=False)
        and not data.get("errors")
    ):
        data.pop("errors")

    return data
