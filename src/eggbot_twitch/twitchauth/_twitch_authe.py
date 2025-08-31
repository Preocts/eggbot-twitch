from __future__ import annotations

import requests

from .authentication import Authentication
from .authorization import Authorization

_AUTHO_TOKEN_URL = "https://id.twitch.tv/oauth2/token"


def get_authentication(
    twitch_app_client_id: str,
    twitch_app_client_secret: str,
    redirect_url: str,
    authorization: Authorization,
) -> Authentication | None:
    """
    Get bearer authentication from a user authorization.

    Used to request a new authentication for the app only when no prior authentication
    exists or an authentication refresh is rejected. Requires user authorization grant.

    Args:
        twitch_app_client_id: The registered Twitch app id
        twitch_app_client_secret: The registered Twitch app secret
        redirect_url: The registered Twitch app redirect url
        authorization: The resulting Authorization from a user auth request
    """
    if authorization.error:
        return None

    data = {
        "client_id": twitch_app_client_id,
        "client_secret": twitch_app_client_secret,
        "code": authorization.code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_url,
    }

    response = requests.post(_AUTHO_TOKEN_URL, data=data)

    if not response.ok:
        return None

    try:
        return Authentication.parse_response(response.json())

    except KeyError:
        return None
