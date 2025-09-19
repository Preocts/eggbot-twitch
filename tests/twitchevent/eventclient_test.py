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
from eggbot_twitch.twitchevent import end_session_thread
from eggbot_twitch.twitchevent import start_session_thread

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

        message = copy.deepcopy(MOCK_HANDSHAKE_RESPONSE)
        message["payload"]["session"]["id"] = f"mock_session_id:{client.uid}"
        client.send_queue.put(json.dumps(message))

        while self.is_serving.is_set():
            try:
                send_message = client.send_queue.get(timeout=0.1)
                client.connection.send(send_message)

            except TimeoutError:
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
    sessionid: str | None = None

    try:
        sessionid = start_session_thread(HOST, PORT)

    finally:
        end_session_thread(sessionid)

    assert sessionid.startswith("mock_session_id")


def test_start_session_thread_hard_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the failsafe hard timeout that prevents an infinate block on starting sessions."""
    monkeypatch.setattr(eventclient_module, "_CONNECTION_TIMEOUT_SECONDS", 0.0)
    pattern = "Connection to session hit max timeout."
    sessionid: str | None = None

    try:
        with pytest.raises(TimeoutError, match=pattern):
            start_session_thread(HOST, PORT)

    finally:
        end_session_thread(sessionid)


def test_start_session_retries_and_fails_without_server() -> None:
    pattern = "Failed to establish connection to websocket server after 3 retries"

    with pytest.raises(ConnectionError, match=pattern):
        start_session_thread(HOST, PORT + 1)
