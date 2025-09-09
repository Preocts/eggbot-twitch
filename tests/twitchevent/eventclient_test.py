from __future__ import annotations

import threading
import time
from functools import partial

from websockets.sync.server import ServerConnection
from websockets.sync.server import serve


class MockEventServer(threading.Thread):

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.timeout_at = time.time() + 2

    def run(self) -> None:
        """Run the websocket server forever."""
        handler = partial(self.message_handler, self.timeout_at)
        with serve(handler, self.host, self.port) as server:
            self.server = server
            self.server.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()

    @staticmethod
    def message_handler(timeout_at: float, websocket: ServerConnection) -> None:
        while time.time() < timeout_at:
            message = websocket.recv()

            print(f"Recieved: {message=}")

        websocket.close()
