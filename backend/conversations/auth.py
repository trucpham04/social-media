from __future__ import annotations

from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework_simplejwt.authentication import JWTAuthentication


def _get_raw_token_from_scope(scope) -> Optional[str]:
    query_string = scope.get("query_string") or b""
    if query_string:
        try:
            query_params = dict(
                part.split(b"=", 1) for part in query_string.split(b"&") if b"=" in part
            )
        except ValueError:
            query_params = {}
        token = query_params.get(b"token")
        if token:
            return token.decode()

    headers = dict(scope.get("headers") or [])
    auth_header = headers.get(b"authorization") or headers.get(b"Authorization")
    if auth_header:
        try:
            prefix, token = auth_header.decode().split(" ", 1)
        except ValueError:
            return None
        if prefix.lower() == "bearer":
            return token
    return None


def authenticate_scope(scope) -> Tuple[Optional[HttpRequest], Optional[object]]:
    """
    Authenticate a Channels scope using DRF SimpleJWT's JWTAuthentication.

    Returns a tuple (user, token). User will be an instance of AUTH_USER_MODEL
    or AnonymousUser if no valid token is provided.
    """
    raw_token = _get_raw_token_from_scope(scope)
    if not raw_token:
        return None, None

    authenticator = JWTAuthentication()
    try:
        validated_token = authenticator.get_validated_token(raw_token)
        user = authenticator.get_user(validated_token)
    except Exception:
        return None, None

    return user, validated_token

