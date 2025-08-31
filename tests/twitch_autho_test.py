from __future__ import annotations

import threading
import time
import contextlib
from collections.abc import Generator

import pytest
import requests

from eggbot_twitch import proto


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


@pytest.fixture(autouse=True)
def shorten_autho_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(proto, "_AUTHO_TIMEOUT_SECONDS", 2)


def test_get_autho_code_success() -> None:
    """Validate that autho code is successfully extracted from callback."""
    callback_url = "http://localhost:5005/callback?code=mock_code&scope=user:read:chat+user:read:email&state=123"
    expected = proto.Authorization("123", "mock_code", "user:read:chat user:read:email", "", "")

    with delayed_get_request(1, callback_url):
        authorization = proto.get_autho_code()

    assert authorization == expected


def test_get_autho_code_unsuccess() -> None:
    """Validate that errors are handled."""
    callback_url = "http://localhost:5005/callback?error=access_denied&error_description=The+user+denied+you+access&state=123"
    expected = proto.Authorization("123", "", "", "access_denied", "The user denied you access")

    with delayed_get_request(1, callback_url):
        authorization = proto.get_autho_code()

    assert authorization == expected


def test_get_autho_code_timeout() -> None:
    """Validate that timeout is handled."""
    authorization = proto.get_autho_code()

    assert authorization is None
