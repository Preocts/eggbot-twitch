from __future__ import annotations

import dataclasses
import time
from typing import Any

from ._auth import Auth


@dataclasses.dataclass(frozen=True, slots=True)
class ClientAuth(Auth):
    """Represent the response of a client authorization request"""

    access_token: str
    expires_in: int
    expires_at: int
    token_type: str

    @classmethod
    def parse_response(cls, response: dict[str, Any]) -> ClientAuth:
        """Build from authorization response from TwitchTV."""
        expires_at = int(response["expires_in"] + time.time())

        return cls(
            access_token=response["access_token"],
            expires_in=response["expires_in"],
            expires_at=response.get("expires_at", expires_at),
            token_type=response["token_type"],
        )
