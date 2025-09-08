from __future__ import annotations

from eggbot_twitch.twitchauth import ClientAuth

MOCK_CLIENT_AUTH_RESPONSE = {
    "access_token": "mock_access_token",
    "expires_in": 14124,
    "expires_at": 14126,
    "token_type": "bearer",
}


def test_parse_response() -> None:
    """Test the parsing of a response."""
    userauth = ClientAuth.parse_response(MOCK_CLIENT_AUTH_RESPONSE)

    assert userauth.access_token == "mock_access_token"
    assert userauth.expires_in == 14124
    assert userauth.expires_at == 14126
    assert userauth.token_type == "bearer"
