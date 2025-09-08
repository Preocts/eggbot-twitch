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
    clientauth = ClientAuth.parse_response(MOCK_CLIENT_AUTH_RESPONSE, "mock_id")

    assert clientauth.access_token == "mock_access_token"
    assert clientauth.expires_in == 14124
    assert clientauth.expires_at == 14126
    assert clientauth.token_type == "bearer"
    assert clientauth.client_id == "mock_id"
