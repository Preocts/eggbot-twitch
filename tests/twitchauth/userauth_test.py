from __future__ import annotations

from eggbot_twitch.twitchauth import UserAuth

MOCK_USER_AUTH = {
    "access_token": "mock_access_token",
    "expires_in": 15701,
    "expires_at": 1756875356,
    "refresh_token": "mock_refresh_token",
    "scope": ["user:read:chat", "user:read:email"],
    "token_type": "bearer",
}


def test_parse_response() -> None:
    """Test the parsing of a response."""
    userauth = UserAuth.parse_response(MOCK_USER_AUTH, "mock_id")

    assert userauth.access_token == "mock_access_token"
    assert userauth.expires_in == 15701
    assert userauth.expires_at == 1756875356
    assert userauth.refresh_token == "mock_refresh_token"
    assert userauth.scope == ("user:read:chat", "user:read:email")
    assert userauth.token_type == "bearer"
    assert userauth.client_id == "mock_id"
