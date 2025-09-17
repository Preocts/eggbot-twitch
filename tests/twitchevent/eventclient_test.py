from __future__ import annotations

import copy
import dataclasses
import json
import queue
import threading
import time
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from websockets import Request
from websockets import Response
from websockets.sync.server import Server
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

STOPSERVER = threading.Event()
SENDQUEUE: queue.Queue[PendingMessage] = queue.Queue()


@dataclasses.dataclass
class PendingMessage:
    message: str
    websocket: ServerConnection


class MockMessageSender(threading.Thread):

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        while not STOPSERVER.is_set():
            try:
                pending_message = SENDQUEUE.get(timeout=0.1)
            except queue.Empty:
                continue

            pending_message.websocket.send(pending_message.message)


class MockEventServer(threading.Thread):

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.host = host.replace("ws://", "").replace("wss://", "")
        self.port = port
        self.server: Server | None = None
        self.sender = MockMessageSender()

    def run(self) -> None:
        """Run the websocket server forever."""
        with serve(
            lambda x: None,
            self.host,
            self.port,
            process_response=self.response_hook,
            compression=None,
        ) as server:
            self.sender.start()
            self.server = server
            self.server.serve_forever()

    def shutdown(self) -> None:
        STOPSERVER.set()
        if self.server:  # pragma: no cover
            self.server.shutdown()

    @staticmethod
    def response_hook(
        websocket: ServerConnection,
        request: Request,
        response: Response,
    ) -> Response:
        # Return a handshake with session id on join
        message = copy.deepcopy(MOCK_HANDSHAKE_RESPONSE)
        message["payload"]["session"]["id"] = f"mock_session_id:{uuid.uuid4()}"
        SENDQUEUE.put(PendingMessage(json.dumps(message), websocket))
        return response


HOST = "ws://localhost"
PORT = 5006


@pytest.fixture(scope="session", autouse=True)
def session_for_tests() -> Generator[None, None, None]:
    server = MockEventServer(HOST, PORT)

    try:
        server.start()
        # Give the server time to spin up
        # TODO: Is there *any* way to detect this? Maybe ping the port until an answer?
        time.sleep(2)
        yield None

    finally:
        server.shutdown()


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
    # TODO: Something here is causing a thread exception
    monkeypatch.setattr(eventclient_module, "_CONNECTION_TIMEOUT_SECONDS", 0.0)
    pattern = "Connection to session hit max timeout."
    sessionid: str | None = None

    try:
        with pytest.raises(TimeoutError, match=pattern):
            start_session_thread(HOST, PORT)

    finally:
        end_session_thread(sessionid)


# def test_end_session_thread_with_session_id() -> None:
