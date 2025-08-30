from __future__ import annotations

import threading
import time
import contextlib
from collections.abc import Generator

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


def test_get_autho_code_success() -> None:
    """Validate that autho code is successfully extracted from callback."""
    callback_url = "http://localhost:5005/callback?code=mock_code&scope=user:read:chat+user:read:email&state=123"

    with delayed_get_request(1, callback_url):
        exit_code = proto.get_autho_code()

    assert exit_code == "mock_code"


def test_get_autho_code_unsuccess() -> None:
    """Validate that errors are handled."""
    callback_url = "http://localhost:5005/callback?error=access_denied&error_description=The+user+denied+you+access&state=123"

    with delayed_get_request(1, callback_url):
        exit_code = proto.get_autho_code()

    assert exit_code == ""
