from __future__ import annotations

import json
import logging
import os

import requests

from ._auth import Auth
from .clientauth import ClientAuth
from .userauth import UserAuth
from .userauthgrant import UserAuthGrant

_AUTHO_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
_DEFAULT_USER_AUTH_FILE = "user_auth.json"

logger = logging.getLogger("twitchauth")


def get_authorization(
    twitch_app_client_id: str,
    twitch_app_client_secret: str,
    user_auth: UserAuthGrant | Auth | None = None,
) -> Auth | None:
    """
    Get an auth token from TwitchTV.

    The type of token will depend on the user_auth provided. If a UserAuthGrant is given
    then a new authorization token will be requested, creating a new session. If a
    UserAuth is given, the existing session will be refreshed if possible.

    Args:
        twitch_app_client_id: The registered Twitch app id
        twitch_app_client_secret: The registered Twitch app secret
        user_auth: Either a UserAuthGrant or a Auth object. If None, a client
            authorization is requested.
    """
    if isinstance(user_auth, UserAuthGrant) and user_auth.error:
        return None

    data = {
        "client_id": twitch_app_client_id,
        "client_secret": twitch_app_client_secret,
        "grant_type": "client_credentials",
    }

    if isinstance(user_auth, UserAuthGrant):
        data.update(
            {
                "code": user_auth.code,
                "grant_type": "authorization_code",
                "redirect_uri": user_auth.redirect_url,
            }
        )

    elif isinstance(user_auth, UserAuth):
        data.update(
            {
                "grant_type": "refresh_token",
                "refresh_token": user_auth.refresh_token,
            }
        )

    return _request_token(data, twitch_app_client_id)


def _request_token(data: dict[str, str], client_id: str) -> UserAuth | ClientAuth | None:
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
        if data["grant_type"] == "client_credentials":
            return ClientAuth.parse_response(response.json(), client_id)

        else:
            return UserAuth.parse_response(response.json(), client_id)

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
