from __future__ import annotations

import json
import queue
import threading

import pytest
from websockets import Request
from websockets import Response
from websockets.sync.server import ServerConnection
from websockets.sync.server import serve

from eggbot_twitch.twitchevent import _eventclient as eventclient_module
from eggbot_twitch.twitchevent import end_session_thread
from eggbot_twitch.twitchevent import start_session_thread

MOCK_HANDSHAKE_RESPONSE = {
    "metadata": {
        "message_id": "c7f09613-7b34-4093-b44c-305c6a36bb04",
        "message_type": "session_welcome",
        "message_timestamp": "2025-09-09T03:19:44.99039766Z",
    },
    "payload": {
        "session": {
            "id": "mock_websocket_id",
            "status": "connected",
            "connected_at": "2025-09-09T03:19:44.986763032Z",
            "keepalive_timeout_seconds": 10,
            "reconnect_url": None,
            "recovery_url": None,
        }
    },
}

STEPSERVER = threading.Event()
SENDQUEUE: queue.Queue[str] = queue.Queue()


class MockEventServer(threading.Thread):

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.host = host.replace("ws://", "").replace("wss://", "")
        self.port = port

    def run(self) -> None:
        """Run the websocket server forever."""
        with serve(
            self.message_handler,
            self.host,
            self.port,
            process_response=self.response_hook,
        ) as server:
            self.server = server
            self.server.serve_forever()

    def shutdown(self) -> None:
        STEPSERVER.set()
        self.server.shutdown()

    @staticmethod
    def message_handler(websocket: ServerConnection) -> None:
        while not STEPSERVER.is_set():
            try:
                message = SENDQUEUE.get(timeout=0.1)
            except queue.Empty:
                continue

            websocket.send(message)

        websocket.close()

    @staticmethod
    def response_hook(
        websocket: ServerConnection,
        request: Request,
        response: Response,
    ) -> Response:
        # Return a handshake with session id on join
        SENDQUEUE.put(json.dumps(MOCK_HANDSHAKE_RESPONSE))
        return response


def test_start_session_thread() -> None:
    """Start a session thread and assert the session id is returned"""
    host = "ws://localhost"
    port = 5006
    server = MockEventServer(host, port)
    sessionid: str | None = None

    server.start()

    try:
        sessionid = start_session_thread(host, port)

    finally:
        end_session_thread(sessionid)
        server.shutdown()
        server.join()

    assert sessionid == "mock_websocket_id"


def test_start_session_thread_hard_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the failsafe hard timeout that prevents an infinate block on starting sessions."""
    host = "ws://localhost"
    port = 5006
    monkeypatch.setattr(eventclient_module, "_CONNECTION_TIMEOUT_SECONDS", 0.0)
    pattern = "Connection to session hit max timeout."

    with pytest.raises(TimeoutError, match=pattern):
        start_session_thread(host, port)

