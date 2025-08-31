from __future__ import annotations

from .authentication import Authentication
from .authorization import Authorization


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
    return Authentication()
