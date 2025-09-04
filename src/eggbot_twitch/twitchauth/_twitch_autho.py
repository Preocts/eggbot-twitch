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
    redirect_url: str,
    userauthgrant: UserAuthGrant,
) -> UserAuth | None:
    """
    Get bearer authorization from a user grant.

    Used to request a new authorization for the app only when no prior authorization
    exists or an authorization refresh is rejected. Requires user authorization grant.

    Args:
        twitch_app_client_id: The registered Twitch app id
        twitch_app_client_secret: The registered Twitch app secret
        redirect_url: The registered Twitch app redirect url
        usergrant: The resulting UserAuthGrant from a user auth request
    """
    if userauthgrant.error:
        return None

    data = {
        "client_id": twitch_app_client_id,
        "client_secret": twitch_app_client_secret,
        "code": userauthgrant.code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_url,
    }

    response = requests.post(_AUTHO_TOKEN_URL, data=data)

    if not response.ok:
        logger.error(
            "Request for authorizatoin token failed: (%d) %s",
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
