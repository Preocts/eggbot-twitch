from __future__ import annotations

import json
import tempfile

from eggbot_twitch.twitchauth import UserAuth

MOCK_USER_AUTH = {
    "access_token": "mock_access_token",
    "expires_in": 15701,
    "expires_at": 1756875356,
    "refresh_token": "mock_refresh_token",
    "scope": ["user:read:chat", "user:read:email"],
    "token_type": "bearer",
}


def test_load_valid_file() -> None:
    with tempfile.TemporaryFile() as authfile:
        authfile.write(json.dumps(MOCK_USER_AUTH).encode())
        authfile.read()
        authfile.seek(0)

        userauth = UserAuth.load(authfile)

    assert userauth.access_token == "mock_access_token"
    assert userauth.expires_in == 15701
    assert userauth.expires_at == 1756875356
    assert userauth.refresh_token == "mock_refresh_token"
    assert userauth.scope == ("user:read:chat", "user:read:email")
    assert userauth.token_type == "bearer"


def test_dump() -> None:
    auth = UserAuth.parse_response(MOCK_USER_AUTH)
    with tempfile.TemporaryFile() as authfile:
        auth.dump(authfile)
        authfile.seek(0)

        results = authfile.read()

    assert json.loads(results.decode()) == MOCK_USER_AUTH
