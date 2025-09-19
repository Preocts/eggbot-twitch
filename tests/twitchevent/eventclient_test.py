from __future__ import annotations

import copy
import dataclasses
import json
import queue
import threading
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from websockets.sync.server import ServerConnection
from websockets.sync.server import serve

from eggbot_twitch.twitchevent import _eventclient as eventclient_module
from eggbot_twitch.twitchevent import get_session

MOCK_HANDSHAKE_RESPONSE: dict[str, Any] = {
    "metadata": {
        "message_id": "c7f09613-7b34-4093-b44c-305c6a36bb04",
        "message_type": "session_welcome",
        "message_timestamp": "2025-09-09T03:19:44.99039766Z",
    },
    "payload": {
        "session": {
            "id": "mock_session_id",
            "status": "connected",
            "connected_at": "2025-09-09T03:19:44.986763032Z",
            "keepalive_timeout_seconds": 10,
            "reconnect_url": None,
            "recovery_url": None,
        }
    },
}

MOCK_NOTIFICATION_RESPONSE: dict[str, Any] = {
    "metadata": {
        "message_id": "befa7b53-d79d-478f-86b9-120f112b044e",
        "message_type": "notification",
        "message_timestamp": "2022-11-16T10:11:12.464757833Z",
        "subscription_type": "channel.follow",
        "subscription_version": "1",
    },
    "payload": {
        "subscription": {
            "id": "f1c2a387-161a-49f9-a165-0f21d7a4e1c4",
            "status": "enabled",
            "type": "channel.follow",
            "version": "1",
            "cost": 1,
            "condition": {"broadcaster_user_id": "12826"},
            "transport": {"method": "websocket", "session_id": "AQoQexAWVYKSTIu4ec_2VAxyuhAB"},
            "created_at": "2022-11-16T10:11:12.464757833Z",
        },
        "event": {
            "user_id": "1337",
            "user_login": "awesome_user",
            "user_name": "Awesome_User",
            "broadcaster_user_id": "12826",
            "broadcaster_user_login": "twitch",
            "broadcaster_user_name": "Twitch",
            "followed_at": "2023-07-15T18:16:11.17106713Z",
        },
    },
}

MOCK_RECONNECT_RESPONSE: dict[str, Any] = {
    "metadata": {
        "message_id": "84c1e79a-2a4b-4c13-ba0b-4312293e9308",
        "message_type": "session_reconnect",
        "message_timestamp": "2022-11-18T09:10:11.634234626Z",
    },
    "payload": {
        "session": {
            "id": "AQoQexAWVYKSTIu4ec_2VAxyuhAB",
            "status": "reconnecting",
            "keepalive_timeout_seconds": None,
            "reconnect_url": "wss://eventsub.wss.twitch.tv?...",
            "connected_at": "2022-11-16T10:11:12.634234626Z",
        }
    },
}

MOCK_REVOCATION_RESPONSE: dict[str, Any] = {
    "metadata": {
        "message_id": "84c1e79a-2a4b-4c13-ba0b-4312293e9308",
        "message_type": "revocation",
        "message_timestamp": "2022-11-16T10:11:12.464757833Z",
        "subscription_type": "channel.follow",
        "subscription_version": "1",
    },
    "payload": {
        "subscription": {
            "id": "f1c2a387-161a-49f9-a165-0f21d7a4e1c4",
            "status": "authorization_revoked",
            "type": "channel.follow",
            "version": "1",
            "cost": 1,
            "condition": {"broadcaster_user_id": "12826"},
            "transport": {"method": "websocket", "session_id": "AQoQexAWVYKSTIu4ec_2VAxyuhAB"},
            "created_at": "2022-11-16T10:11:12.464757833Z",
        }
    },
}

MOCK_KEEPALIVE_RESPONSE: dict[str, Any] = {
    "metadata": {
        "message_id": "84c1e79a-2a4b-4c13-ba0b-4312293e9308",
        "message_type": "session_keepalive",
        "message_timestamp": "2023-07-19T10:11:12.634234626Z",
    },
    "payload": {},
}


@dataclasses.dataclass(frozen=True)
class Client:
    uid: str
    connection: ServerConnection
    send_queue: queue.Queue[str] = dataclasses.field(default_factory=queue.Queue)


class MockEventServer(threading.Thread):

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.host = host.replace("ws://", "").replace("wss://", "")
        self.port = port
        self.server = serve(self.handler, self.host, self.port)

        self.is_serving = threading.Event()
        self.clients: set[Client] = set()

    def run(self) -> None:
        """Run the websocket server forever."""
        self.is_serving.set()
        self.server.serve_forever()

    def handler(self, websocket: ServerConnection) -> None:
        # Runs in a thread on client connection, handled by server
        client = Client(str(uuid.uuid4()), websocket)

        messages = [
            copy.deepcopy(MOCK_HANDSHAKE_RESPONSE),
            copy.deepcopy(MOCK_NOTIFICATION_RESPONSE),
            copy.deepcopy(MOCK_RECONNECT_RESPONSE),
            copy.deepcopy(MOCK_REVOCATION_RESPONSE),
            copy.deepcopy(MOCK_KEEPALIVE_RESPONSE),
        ]

        for message in messages:
            if "session" in message["payload"]:
                message["payload"]["session"]["id"] = f"mock_session_id:{client.uid}"
            client.send_queue.put(json.dumps(message))

        while self.is_serving.is_set():
            try:
                send_message = client.send_queue.get(timeout=0.1)
                client.connection.send(send_message)

            except queue.Empty:
                continue


HOST = "ws://localhost"
PORT = 5006


@pytest.fixture(scope="session", autouse=True)
def session_for_tests() -> Generator[None, None, None]:
    server = MockEventServer(HOST, PORT)

    try:
        server.start()
        yield None

    finally:
        server.is_serving.clear()
        server.server.shutdown()
        server.join()


def test_start_session_thread() -> None:
    """Start a session thread and assert the session id is returned"""
    session = get_session(HOST, PORT)
    messages = [message for message in session.message_iter()]
    session.close()

    assert session.session_id.startswith("mock_session_id")
    assert len(messages) == 4


def test_start_session_thread_hard_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the failsafe hard timeout that prevents an infinate block on starting sessions."""
    monkeypatch.setattr(eventclient_module, "_CONNECTION_TIMEOUT_SECONDS", 0.0)
    pattern = "Connection to session hit max timeout."

    with pytest.raises(TimeoutError, match=pattern):
        get_session(HOST, PORT)


def test_start_session_retries_and_fails_without_server() -> None:
    pattern = "Failed to establish connection to websocket server after 3 retries"

    with pytest.raises(ConnectionError, match=pattern):
        get_session(HOST, PORT + 1)
