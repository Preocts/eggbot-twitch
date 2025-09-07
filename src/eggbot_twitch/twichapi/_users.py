"""Talk to the API's User category."""

from __future__ import annotations

from typing import TYPE_CHECKING

import requests

_BASE_URL = "https://api.twitch.tv/helix"

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any
    from typing import Protocol

    class AuthType(Protocol):
        """Any Auth object that provides an 'access_token' attribute."""

        @property
        def access_token(self) -> str: ...


def get_users_raw(
    client_id: str,
    auth: AuthType,
    *,
    user_ids: Sequence[str] | None = None,
    user_logins: Sequence[str] | None = None,
) -> dict[str, Any]:
    """
    Get raw response of user data given a maximum of 100 user ids or user logins.

    Source:
        https://dev.twitch.tv/docs/api/reference/#get-users

    Authorization:
        Requires an app access token or user access token.

    Args:
        auth: Any Auth object that provides an 'access_token' attribute.
        user_ids: A sequence of string user ids.
        user_logins: A sequence of string user logins (user names).
    """
    if len(user_ids or []) + len(user_logins or []) > 100:
        raise ValueError("Total number of user_ids and user_logins exceeded 100.")

    url = _BASE_URL + "/users"
    headers = {
        "Authorization": f"Bearer {auth.access_token}",
        "Client-Id": client_id,
    }

    params = {
        "id": user_ids if user_ids else [],
        "login": user_logins if user_logins else [],
    }

    response = requests.get(url, params=params, headers=headers)

    return response.json()
