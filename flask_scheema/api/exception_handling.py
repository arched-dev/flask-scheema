from flask import Response
from werkzeug.exceptions import HTTPException

from flask_scheema.api.responses import create_response
from flask_scheema.utilities import get_config_or_model_meta


def handle_http_exception(e: HTTPException) -> Response:
    """
        Handles HTTP exceptions and returns a standardised response.


    Args:
        e: The HTTP exception instance.

    Returns:
        Standardised response.
    """

    print_exc = get_config_or_model_meta(key="API_PRINT_EXCEPTIONS", default=True)
    if print_exc:
        import traceback
        print(e)
        traceback.print_exc()

    return create_response(
        status=e.code, errors=[{"error": e.name, "reason": e.description}]
    )
