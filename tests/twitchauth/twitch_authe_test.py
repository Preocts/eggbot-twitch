from __future__ import annotations

import pytest

from eggbot_twitch.twitchauth import Authentication
from eggbot_twitch.twitchauth import Authorization
from eggbot_twitch.twitchauth import get_authentication


@pytest.fixture
def valid_autho() -> Authorization:
    return Authorization("123", "mock_code", "user:email:read")


def test_get_authentication_success(valid_autho) -> None:

    authe = get_authentication(valid_autho)

    assert isinstance(authe, Authentication)
