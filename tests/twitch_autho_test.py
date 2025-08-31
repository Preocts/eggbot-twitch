from __future__ import annotations

import contextlib
import io
import threading
import time
from collections.abc import Generator

import requests

from eggbot_twitch.twitchauth import Authorization
from eggbot_twitch.twitchauth import get_autho_code


@contextlib.contextmanager
def delayed_get_request(delay: int, url: str) -> Generator[None, None, None]:
    """Spin up a thread that fires a GET to 'url' after 'delay' seconds."""

    def send_request_delayed(delay: int, url: str) -> None:
        time.sleep(delay)
        requests.get(url)

    thread = threading.Thread(target=send_request_delayed, args=(delay, url))
    try:
        thread.start()
        yield None

    finally:
        thread.join()


def test_get_autho_code_success() -> None:
    """Validate that autho code is successfully extracted from callback."""
    callback_url = "http://localhost:5005/callback?code=mock_code&scope=user:read:chat+user:read:email&state=123"
    expected_autho = Authorization("123", "mock_code", "user:read:chat user:read:email")
    expected_stdout = "https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=mock&redirect_uri=http://localhost:5005/callback&scope=user%3Aread%3Achat%20user%3Aread%3Aemail&state="
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        with delayed_get_request(1, callback_url):
            authorization = get_autho_code(
                callback_host="localhost",
                callback_port=5005,
                twitch_app_client_id="mock",
                redirect_url="http://localhost:5005/callback",
                scope="user:read:chat user:read:email",
                timeout=2,
            )

    assert authorization == expected_autho
    assert expected_stdout in stdout.getvalue()


def test_get_autho_code_unsuccess() -> None:
    """Validate that errors are handled."""
    callback_url = "http://localhost:5005/callback?error=access_denied&error_description=The+user+denied+you+access&state=123"
    expected = Authorization("123", "", "", "access_denied", "The user denied you access")

    with delayed_get_request(1, callback_url):
        authorization = get_autho_code(
            callback_host="localhost",
            callback_port=5005,
            twitch_app_client_id="mock",
            redirect_url="http://localhost:5005/callback",
            scope="user:read:chat user:read:email",
            timeout=2,
        )

    assert authorization == expected


def test_get_autho_code_timeout() -> None:
    """Validate that timeout is handled."""
    authorization = get_autho_code(
        callback_host="localhost",
        callback_port=5005,
        twitch_app_client_id="mock",
        redirect_url="http://localhost:5005/callback",
        scope="user:read:chat user:read:email",
        timeout=1,
    )

    assert authorization is None
