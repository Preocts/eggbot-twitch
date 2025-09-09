from __future__ import annotations

import json

import websockets.sync.client


def get_session_id(host: str, port: int) -> str:
    """PROTO: Connect to a websocket server, see the results."""

    with websockets.sync.client.connect(f"ws://{host}:{port}") as websocket:
        message = websocket.recv(timeout=3)
        _message = json.loads(message)

    return _message["payload"]["session"]["id"]
