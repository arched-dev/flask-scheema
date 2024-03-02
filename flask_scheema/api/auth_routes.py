from functools import wraps
from typing import Callable, Union, List

from database_operations import User
from flask import abort, Blueprint, g, current_app, request
from flask_scheema.src.flask_scheema.api.decorators import handle_one, auth_required, handle_error, HTTP_UNAUTHORIZED
from services import auth_service
from webserv.extensions import scheema
from webserv.schemas.mallow import (
    TokenRefreshSchema,
    LoginInputSchema,
    RefreshInputSchema,
    ResetPasswordSchemaIn,
    ResetPasswordSchemaOut, UserSchema,
)

auth = Blueprint("auth", __name__, url_prefix="/api")


@auth.route("/login", methods=["POST"])
@scheema.scheema_constructor(
    input_schema=LoginInputSchema,
    output_schema=TokenRefreshSchema,
    model=User,
    group_tag="Portal",
    handler=handle_one
)
def login(deserialised_data=None):
    """
    Login User
    ---
    Logs in a user, returning a refresh token and access token
    """
    auth = auth_service.login_user(deserialised_data)
    if auth:
        return auth

    abort(401, "Invalid credentials")


@auth.route("/reset", methods=["POST"])
@scheema.scheema_constructor(
    input_schema=ResetPasswordSchemaIn,
    output_schema=ResetPasswordSchemaOut,
    model=User,
    handler=handle_one,
    authentication=None,
    roles=False,
    group_tag="Portal",
)
def reset_password(deserialised_data=None):
    """
    Reset Password
    ---
    Resets a user's password and emails them a temporary password that will expire in 1 hour.
    This password must be changed upon login.
    """
    result = auth_service.reset_user(deserialised_data)
    if result:
        return result
    abort(401, "Invalid credentials")


def refresh_auth_required(roles: Union[bool, List[str]]) -> Callable:
    """
    A decorator to check if the data has the required auth data.
    Args:
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

            do_auth = current_app.extensions["flask_scheema"].get_config("API_AUTHENTICATE", False)
            if do_auth is False or roles is False:
                return f(*args, **kwargs)

            data = request.json
            if "refresh_token" not in data or data["refresh_token"] == "":
                resp = handle_error("Token not present expired", HTTP_UNAUTHORIZED)
                resp.headers["WWW-Authenticate"] = 'Bearer error="invalid_token"'
                return resp

            return f(*args, **kwargs)

        # this is so we can register the auth_required header details with the api spec
        if not hasattr(wrapped, "_decorators"):
            wrapped._decorators = []

        wrapped._decorators.append(refresh_auth_required)
        auth_required._args = roles if roles else []

        return wrapped

    return decorator


@auth.route("/refresh", methods=["POST"])
@scheema.scheema_constructor(
    input_schema=RefreshInputSchema,
    output_schema=TokenRefreshSchema,
    model=User,
    authentication=refresh_auth_required,
    roles=True,
    handler=handle_one,
    group_tag="Portal",
)
def refresh(deserialised_data=None):
    """
    Refresh Access Token
    ---
    Refreshes an access token, returning a new access token and refresh token
    """
    result = auth_service.refresh_access_token(deserialised_data)
    if result:
        return result
    abort(401, "Token is invalid")


@auth.route("/users/current", methods=["GET"])
@scheema.scheema_constructor(
    output_schema=UserSchema,
    model=User,
    handler=handle_one,
    authentication=auth_required,
    roles=True,
    group_tag="Portal",
)
def get_current_user():
    """
    GET /api/users/current
    ---
    Returns the current `user` from the database"""
    return g.get("current_user") or abort(403)
