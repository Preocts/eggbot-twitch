from __future__ import annotations

import requests

from .userauth import UserAuth
from .userauthgrant import UserAuthGrant

_AUTHO_TOKEN_URL = "https://id.twitch.tv/oauth2/token"


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
        return None

    try:
        return UserAuth.parse_response(response.json())

    except KeyError:
        return None
