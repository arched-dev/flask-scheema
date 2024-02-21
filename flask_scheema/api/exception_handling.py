from flask import Response
from werkzeug.exceptions import HTTPException

from flask_scheema.api.responses import create_response


def handle_http_exception(e: HTTPException) -> Response:
    """
        Handles HTTP exceptions and returns a standardised response.


    Args:
        e: The HTTP exception instance.

    Returns:
        Standardised response.
    """
    return create_response(
        status=e.code, error={"error": e.name, "reason": e.description}
    )
