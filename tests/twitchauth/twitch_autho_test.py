from __future__ import annotations

import copy
import json
import tempfile
import time
from collections.abc import Generator

import pytest
import responses
import responses.matchers

from eggbot_twitch.twitchauth import UserAuth
from eggbot_twitch.twitchauth import UserAuthGrant
from eggbot_twitch.twitchauth import get_authorization
from eggbot_twitch.twitchauth import load_user_authorization
from eggbot_twitch.twitchauth import save_user_authorization

MOCK_AUTHE_RESPONSE = {
    "access_token": "mock_access_token",
    "expires_in": 14124,
    "refresh_token": "mock_refresh_token",
    "scope": [
        "user:email:read",
    ],
    "token_type": "bearer",
}


@pytest.fixture
def valid_grant() -> UserAuthGrant:
    return UserAuthGrant(
        state="123",
        redirect_url="http://localhost:5005/callback",
        code="mock_code",
        scope="user:email:read",
    )


@pytest.fixture
def invalid_grant() -> UserAuthGrant:
    return UserAuthGrant(
        state="123",
        redirect_url="http://localhost:5005/callback",
        code="",
        scope="",
        error="error",
        error_description="user denied",
    )


@pytest.fixture
def userauthfilename() -> Generator[str, None, None]:
    """Create a tempfile with a user auth saved in it, yield the filename."""
    with tempfile.NamedTemporaryFile() as authfile:
        authfile.write(json.dumps(MOCK_AUTHE_RESPONSE).encode())
        authfile.seek(0)
        yield authfile.name


@responses.activate(assert_all_requests_are_fired=True)
def test_get_authorization_success(
    valid_grant: UserAuthGrant,
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

    userauth = get_authorization(
        twitch_app_client_id="mock_id",
        twitch_app_client_secret="mock_secret",
        user_auth=valid_grant,
    )

    assert isinstance(userauth, UserAuth)
    assert userauth.access_token == "mock_access_token"
    assert userauth.expires_in == 14124
    assert userauth.expires_at == int(14124 + static_time)
    assert userauth.refresh_token == "mock_refresh_token"
    assert userauth.scope == ("user:email:read",)
    assert userauth.token_type == "bearer"


@responses.activate(assert_all_requests_are_fired=True)
def test_get_authorization_failure(valid_grant: UserAuthGrant) -> None:
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

    userauth = get_authorization(
        twitch_app_client_id="mock_id",
        twitch_app_client_secret="mock_secret",
        user_auth=valid_grant,
    )

    assert userauth is None


@responses.activate(assert_all_requests_are_fired=True)
def test_get_authorization_invalid_response(valid_grant: UserAuthGrant) -> None:
    mock_resp = copy.deepcopy(MOCK_AUTHE_RESPONSE)
    del mock_resp["refresh_token"]

    responses.add(
        method="POST",
        url="https://id.twitch.tv/oauth2/token",
        body=json.dumps(mock_resp),
    )

    userauth = get_authorization(
        twitch_app_client_id="mock_id",
        twitch_app_client_secret="mock_secret",
        user_auth=valid_grant,
    )

    assert userauth is None


@responses.activate
def test_get_authorization_invalid_grant(invalid_grant) -> None:

    responses.add(
        method="POST",
        url="https://id.twitch.tv/oauth2/token",
        body=AssertionError("requests.post should NOT have been called."),
    )

    userauth = get_authorization(
        twitch_app_client_id="mock_id",
        twitch_app_client_secret="mock_secret",
        user_auth=invalid_grant,
    )

    assert userauth is None


@responses.activate(assert_all_requests_are_fired=True)
def test_get_authorization_refresh_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the success of a fresh request. A new UserAuth object should be returned."""
    # Authentication calculates time to expires so we need a static, testable time.
    static_time = 100.0
    monkeypatch.setattr(time, "time", lambda: static_time)
    user_auth = UserAuth.parse_response(MOCK_AUTHE_RESPONSE)

    mock_response = json.dumps(MOCK_AUTHE_RESPONSE | {"access_token": "new_mock_access_token"})

    params_match = {
        "client_id": "mock_id",
        "client_secret": "mock_secret",
        "grant_type": "refresh_token",
        "refresh_token": "mock_refresh_token",
    }

    responses.add(
        method="POST",
        url="https://id.twitch.tv/oauth2/token",
        body=mock_response,
        match=[responses.matchers.urlencoded_params_matcher(params_match)],
    )

    new_user_auth = get_authorization(
        twitch_app_client_id="mock_id",
        twitch_app_client_secret="mock_secret",
        user_auth=user_auth,
    )

    assert isinstance(new_user_auth, UserAuth)
    assert new_user_auth is not user_auth
    assert new_user_auth.access_token == "new_mock_access_token"
    assert new_user_auth.expires_in == 14124
    assert new_user_auth.expires_at == int(14124 + static_time)
    assert new_user_auth.refresh_token == "mock_refresh_token"
    assert new_user_auth.scope == ("user:email:read",)
    assert new_user_auth.token_type == "bearer"


def test_load_user_authorization_success_filename(userauthfilename: str) -> None:
    """Load a generated file by provided filename"""

    userauth = load_user_authorization(userauthfilename)

    assert isinstance(userauth, UserAuth)


def test_load_user_authorization_success_environ(
    userauthfilename: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Load a generated file by provided environment variable"""
    monkeypatch.setenv("EGGBOT_TWITCH_USER_AUTH_FILE", userauthfilename)

    userauth = load_user_authorization()

    assert isinstance(userauth, UserAuth)


def test_load_user_authorization_invalid_file_format() -> None:
    """Handle invalid file formats and expect None as a result."""
    userauth = load_user_authorization(".gitignore")

    assert userauth is None


def test_load_user_authorization_missing_file() -> None:
    """Handle when authorization file does not exist"""
    userauth = load_user_authorization("/path/not/exists")

    assert userauth is None


def test_save_user_authorization_success(userauthfilename: str) -> None:
    """Save user authorization to a file."""
    expected = copy.deepcopy(MOCK_AUTHE_RESPONSE)
    expected["access_token"] = "newmocktoken"
    userauth = UserAuth.parse_response(expected)

    save_user_authorization(userauth, userauthfilename)

    with open(userauthfilename, "rb") as infile:
        result = json.load(infile)

    assert result["access_token"] == "newmocktoken"
