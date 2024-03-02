from functools import wraps
from typing import Callable, List

import jwt
from flask import request, abort, g, current_app
from jwt import ExpiredSignatureError, DecodeError
from sqlalchemy.sql import roles
from werkzeug.local import LocalProxy

from flask_scheema.api.decorators import handle_error, HTTP_UNAUTHORIZED, HTTP_INTERNAL_SERVER_ERROR
from flask_scheema.utilities import get_config_or_model_meta


def check_roles(user, roles: List[str]):
    """
        Check if the user has the required roles.

    Args:
        user (User): The user object.
        roles (List[str]): List of roles required to access the route.

    Returns:
        bool: True if the user has the required roles, False otherwise.

    """
    return "superuser" in user.role_names or any(
        role in roles for role in user.role_names
    )


def validate_token(token: str):
    """
    Validate the token and return the data.
    Args:
        token (str): The token to be validated.

    Returns:
        dict: The data in the token.
    """

    return jwt.decode(
        token.replace("Bearer ", ""),
        current_app.config["SECRET_KEY"],
        algorithms=["HS256"],
    )


def auth_required(*args, **kwargs) -> Callable:
    """
    A decorator to check if the user is authenticated and has the required roles.
    Args:
        self
        roles (Union[bool, List[str]]):
            - False: No authentication required.
            - True: Only authentication is checked.
            - List of roles: Authentication and role-based access are checked.

    Returns:
        Callable: The decorated function.

    Raises:
        HTTPException: If the user is not authenticated or does not have the required roles.
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args, **kwargs):

            token = request.headers.get("Authorization")
            if not token:
                abort(HTTP_UNAUTHORIZED)

            try:
                data = validate_token(token)
                user_model = get_config_or_model_meta("API_USER_MODEL", default=None)
                user = user_model.query.filter_by(email=data["email"]).first()
                g.current_user = user
                return f(*args, **kwargs)

            except ExpiredSignatureError:
                resp = handle_error("Token has expired", HTTP_UNAUTHORIZED)
                resp.headers["WWW-Authenticate"] = 'Bearer error="invalid_token"'
                return resp
            except DecodeError:
                resp = handle_error("Token is invalid", HTTP_UNAUTHORIZED)
                resp.headers["WWW-Authenticate"] = 'Bearer error="invalid_token"'
            except Exception as e:
                return handle_error(e, HTTP_INTERNAL_SERVER_ERROR)

        # this is so we can register the auth_required header details with the api spec
        if not hasattr(wrapped, "_decorators"):
            wrapped._decorators = []

        wrapped._decorators.append(auth_required)
        auth_required._args = roles if roles else []

        return wrapped

    return decorator


def get_current_user():
    return getattr(g, 'current_user', None)


# Create a `current_user` proxy that uses the `get_current_user` function
current_user = LocalProxy(get_current_user)
