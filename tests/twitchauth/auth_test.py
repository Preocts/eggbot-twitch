from __future__ import annotations

import copy
import dataclasses
import json
import tempfile
import time
from typing import Any

from eggbot_twitch.twitchauth import Auth

MOCK_USER_AUTH = {
    "access_token": "mock_access_token",
    "expires_in": 15701,
    "expires_at": 1756875356,
}


@dataclasses.dataclass(frozen=True, slots=True)
class MockAuth(Auth):
    """Mock Auth child class for testing shared implementation."""

    @classmethod
    def parse_response(cls, response: dict[str, Any], client_id: str) -> MockAuth:
        """Build from authorization response from TwitchTV."""
        expires_at = int(response["expires_in"] + time.time())

        return cls(
            access_token=response["access_token"],
            expires_in=response["expires_in"],
            expires_at=response.get("expires_at", expires_at),
            client_id=client_id,
        )


def test_load_valid_file() -> None:
    with tempfile.TemporaryFile() as authfile:
        contents = copy.deepcopy(MOCK_USER_AUTH)
        contents["client_id"] = "mock_id"
        authfile.write(json.dumps(contents).encode())
        authfile.read()
        authfile.seek(0)

        userauth = MockAuth.load(authfile)

    assert userauth.access_token == "mock_access_token"
    assert userauth.expires_in == 15701
    assert userauth.expires_at == 1756875356
    assert userauth.client_id == "mock_id"


def test_dump() -> None:
    expected = copy.deepcopy(MOCK_USER_AUTH)
    expected["client_id"] = "mock_id"

    auth = MockAuth.parse_response(MOCK_USER_AUTH, "mock_id")
    with tempfile.TemporaryFile() as authfile:
        auth.dump(authfile)
        authfile.seek(0)

        results = authfile.read()

    assert json.loads(results.decode()) == expected


def test_headers_property() -> None:
    expected_headers = {
        "Authorization": "Bearer mock_access_token",
        "Client-Id": "mock_id",
    }

    auth = MockAuth.parse_response(MOCK_USER_AUTH, "mock_id")

    assert auth.headers == expected_headers
