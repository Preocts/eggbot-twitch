from __future__ import annotations

import json
import logging
import os

import requests

from .userauth import UserAuth
from .userauthgrant import UserAuthGrant

_AUTHO_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
_DEFAULT_USER_AUTH_FILE = "user_auth.json"

logger = logging.getLogger("twitchauth")


def get_user_authorization(
    twitch_app_client_id: str,
    twitch_app_client_secret: str,
    user_auth: UserAuth | UserAuthGrant,
    redirect_url: str | None = None,
) -> UserAuth | None:
    """
    Get a new bearer authorization from a user grant or refresh existing auth.

    Args:
        twitch_app_client_id: The registered Twitch app id
        twitch_app_client_secret: The registered Twitch app secret
        user_auth: Either a UserAuthGrant or a UserAuth object. The former will request
            a new authorization. The latter will attempt to refresh an existing authorization.
        redirect_url: The registered Twitch app redirect url. Only needed with UserAuthGrant.
    """
    if isinstance(user_auth, UserAuthGrant) and user_auth.error:
        return None

    if isinstance(user_auth, UserAuthGrant):
        data = {
            "client_id": twitch_app_client_id,
            "client_secret": twitch_app_client_secret,
            "code": user_auth.code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_url or "",
        }

    else:
        data = {
            "client_id": twitch_app_client_id,
            "client_secret": twitch_app_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": user_auth.refresh_token,
        }

    return _request_token(data)


def _request_token(data: dict[str, str]) -> UserAuth | None:
    """Request a token, either new or a refresh, given the API data to post."""
    response = requests.post(_AUTHO_TOKEN_URL, data=data)

    if not response.ok:
        logger.error(
            "Request for authorization token failed: (%d) %s",
            response.status_code,
            response.text,
        )
        return None

    try:
        return UserAuth.parse_response(response.json())

    except KeyError:
        logger.error("Unable to parse unexpected response format.")
        return None


def _resolve_user_auth_file(user_auth_file: str | None) -> str:
    """Resovles user_auth_file to provided string, $EGGBOT_TWITCH_USER_AUTH_FILE, or _DEFAULT_USER_AUTH_FILE."""
    return (
        user_auth_file
        if user_auth_file is not None
        else os.getenv("EGGBOT_TWITCH_USER_AUTH_FILE", _DEFAULT_USER_AUTH_FILE)
    )


def load_user_authorization(
    user_auth_file: str | None = None,
) -> UserAuth | None:
    """
    Attempt to load a UserAuth from file.

    Args:
        user_auth_file: The default file is _DEFAULT_USER_AUTH_FILE. Override this
            location by providing a keyword argument or setting the
            'EGGBOT_TWITCH_USER_AUTH_FILE' environment variable.
    """
    user_auth_file = _resolve_user_auth_file(user_auth_file)

    logger.debug("Attempting to load authorization from '%s'", user_auth_file)

    try:
        with open(user_auth_file, "rb") as infile:
            return UserAuth.load(infile)

    except FileNotFoundError:
        return None

    except (OSError, json.JSONDecodeError):
        return None


def save_user_authorization(
    user_authorization: UserAuth,
    user_auth_file: str | None = None,
) -> None:
    """
    Save a UserAuth to file.

    Args:
        user_authorization: The UserAuth object to save
        user_auth_file: The default file is _DEFAULT_USER_AUTH_FILE. Override this
            location by providing a keyword argument or setting the
            'EGGBOT_TWITCH_USER_AUTH_FILE' environment variable.
    """
    user_auth_file = _resolve_user_auth_file(user_auth_file)

    logger.debug("Saving authorization to '%s'", user_auth_file)

    with open(_resolve_user_auth_file(user_auth_file), "wb") as outfile:
        user_authorization.dump(outfile)
