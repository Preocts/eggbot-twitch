from __future__ import annotations

import json
import time

import pytest
import responses
import responses.matchers

from eggbot_twitch.twitchauth import Authentication
from eggbot_twitch.twitchauth import Authorization
from eggbot_twitch.twitchauth import get_authentication

MOCK_AUTHE_RESPONSE = {
    "access_token": "rfx2uswqe8l4g1mkagrvg5tv0ks3",
    "expires_in": 14124,
    "refresh_token": "5b93chm6hdve3mycz05zfzatkfdenfspp1h1ar2xxdalen01",
    "scope": [
        "user:email:read",
    ],
    "token_type": "bearer",
}


@pytest.fixture
def valid_autho() -> Authorization:
    return Authorization("123", "mock_code", "user:email:read")


@responses.activate(assert_all_requests_are_fired=True)
def test_get_authentication_success(
    valid_autho: Authorization,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Authentication calculates time to expires so we need a static, testable time.
    static_time = 100.0
    monkeypatch.setattr(time, "time", lambda: static_time)

    mock_reponse = json.dumps(MOCK_AUTHE_RESPONSE)
    params_match = {
        "client_id": "mock_id",
        "client_secret": "mock_secret",
        "code": "mock_code",
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:5005/callback",
    }

    responses.add(
        method="POST",
        url="https://id.twitch.tv/oauth2/token",
        body=mock_reponse,
        match=[responses.matchers.urlencoded_params_matcher(params_match)],
    )

    authe = get_authentication(
        twitch_app_client_id="mock_id",
        twitch_app_client_secret="mock_secret",
        redirect_url="http://localhost:5005/callback",
        authorization=valid_autho,
    )

    assert isinstance(authe, Authentication)
    assert authe.access_token == "rfx2uswqe8l4g1mkagrvg5tv0ks3"
    assert authe.expires_in == 14124
    assert authe.expires_at == int(14124 + static_time)
    assert authe.refresh_token == "5b93chm6hdve3mycz05zfzatkfdenfspp1h1ar2xxdalen01"
    assert authe.scope == ("user:email:read",)
    assert authe.token_type == "bearer"


@responses.activate(assert_all_requests_are_fired=True)
def test_get_authentication_failure(valid_autho) -> None:
    params_match = {
        "client_id": "mock_id",
        "client_secret": "mock_secret",
        "code": "mock_code",
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:5005/callback",
    }

    responses.add(
        method="POST",
        url="https://id.twitch.tv/oauth2/token",
        status=403,
        body='{"error": "error"}',
        match=[responses.matchers.urlencoded_params_matcher(params_match)],
    )

    authe = get_authentication(
        twitch_app_client_id="mock_id",
        twitch_app_client_secret="mock_secret",
        redirect_url="http://localhost:5005/callback",
        authorization=valid_autho,
    )

    assert authe is None
