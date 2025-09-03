from __future__ import annotations

import dataclasses
import json
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from _typeshed import SupportsRead


@dataclasses.dataclass(frozen=True, slots=True)
class UserAuth:
    """Represent the response of an authorization request"""

    access_token: str
    expires_in: int
    expires_at: int
    refresh_token: str
    scope: tuple[str, ...]
    token_type: str

    @classmethod
    def parse_response(cls, response: dict[str, Any]) -> UserAuth:
        """Build from authorization response from TwitchTV."""
        if "expires_at" in response:
            expires_at = response["expires_at"]
        else:
            expires_at = int(response["expires_in"] + time.time())

        return cls(
            access_token=response["access_token"],
            expires_in=response["expires_in"],
            expires_at=expires_at,
            refresh_token=response["refresh_token"],
            scope=tuple(response["scope"]),
            token_type=response["token_type"],
        )

    @classmethod
    def load(cls, fp: SupportsRead[bytes]) -> UserAuth:
        """Load UserAuth from a file. Must be in JSON format."""
        return cls.parse_response(json.load(fp))
