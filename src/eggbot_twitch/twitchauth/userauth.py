from __future__ import annotations

import dataclasses
import time
from typing import Any

from ._auth import Auth


@dataclasses.dataclass(frozen=True, slots=True)
class UserAuth(Auth):
    """Represent the response of an authorization request with client id"""

    access_token: str
    expires_in: int
    expires_at: int
    refresh_token: str
    scope: tuple[str, ...]
    token_type: str
    client_id: str

    @classmethod
    def parse_response(cls, response: dict[str, Any], client_id: str) -> UserAuth:
        """Build from authorization response from TwitchTV."""
        expires_at = int(response["expires_in"] + time.time())

        return cls(
            access_token=response["access_token"],
            expires_in=response["expires_in"],
            expires_at=response.get("expires_at", expires_at),
            refresh_token=response["refresh_token"],
            scope=tuple(response["scope"]),
            token_type=response["token_type"],
            client_id=client_id,
        )
