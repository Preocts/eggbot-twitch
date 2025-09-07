from __future__ import annotations

import dataclasses
import json

import responses
from responses import matchers

from eggbot_twitch.twichapi import get_users_raw


@dataclasses.dataclass
class MockAuth:
    access_token: str = "mock_access_token"


@responses.activate(assert_all_requests_are_fired=True)
def test_get_users_raw_success() -> None:
    """Successfully fetch user data using both user id and user name to valididate api call."""
    user_ids = ["123", "456"]
    user_logins = ["foo", "bar"]
    client_id = "mock_client_id"

    expected_url = "https://api.twitch.tv/helix/users?id=123&id=456&login=foo&login=bar"
    expected_headers = {
        "Authorization": f"Bearer {MockAuth().access_token}",
        "Client-Id": client_id,
    }
    expected_result = {
        "data": [
            {
                "id": "123",
                "login": "fiz",
                "display_name": "fiz",
                "type": "",
                "broadcaster_type": "partner",
                "description": "Supporting third-party developers building Twitch integrations from chatbots to game integrations.",
                "profile_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-300x300.png",
                "offline_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/3f13ab61-ec78-4fe6-8481-8682cb3b0ac2-channel_offline_image-1920x1080.png",
                "view_count": 5980557,
                "email": "not-real@email.com",
                "created_at": "2016-12-14T20:32:28Z",
            },
            {
                "id": "456",
                "login": "bang",
                "display_name": "bang",
                "type": "",
                "broadcaster_type": "partner",
                "description": "Supporting third-party developers building Twitch integrations from chatbots to game integrations.",
                "profile_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-300x300.png",
                "offline_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/3f13ab61-ec78-4fe6-8481-8682cb3b0ac2-channel_offline_image-1920x1080.png",
                "view_count": 5980557,
                "email": "not-real@email.com",
                "created_at": "2016-12-14T20:32:28Z",
            },
            {
                "id": "789",
                "login": "foo",
                "display_name": "foo",
                "type": "",
                "broadcaster_type": "partner",
                "description": "Supporting third-party developers building Twitch integrations from chatbots to game integrations.",
                "profile_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-300x300.png",
                "offline_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/3f13ab61-ec78-4fe6-8481-8682cb3b0ac2-channel_offline_image-1920x1080.png",
                "view_count": 5980557,
                "email": "not-real@email.com",
                "created_at": "2016-12-14T20:32:28Z",
            },
            {
                "id": "101112",
                "login": "bar",
                "display_name": "bar",
                "type": "",
                "broadcaster_type": "partner",
                "description": "Supporting third-party developers building Twitch integrations from chatbots to game integrations.",
                "profile_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-300x300.png",
                "offline_image_url": "https://static-cdn.jtvnw.net/jtv_user_pictures/3f13ab61-ec78-4fe6-8481-8682cb3b0ac2-channel_offline_image-1920x1080.png",
                "view_count": 5980557,
                "email": "not-real@email.com",
                "created_at": "2016-12-14T20:32:28Z",
            },
        ]
    }

    responses.add(
        method="GET",
        url=expected_url,
        body=json.dumps(expected_result),
        match=[matchers.header_matcher(expected_headers)],
    )

    result = get_users_raw(
        client_id=client_id,
        auth=MockAuth(),
        user_ids=user_ids,
        user_logins=user_logins,
    )

    assert result == expected_result
