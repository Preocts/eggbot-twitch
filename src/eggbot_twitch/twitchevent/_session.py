from __future__ import annotations

import dataclasses
import queue
import threading


@dataclasses.dataclass
class Session:
    """Represents a webscocket session."""

    host: str
    port: int
    active: bool
    session_id: str = ""
    messages: queue.Queue[str] = queue.Queue()
    thread: threading.Thread = threading.Thread()
    stop_flag: threading.Event = threading.Event()
    exception: Exception | None = None

    def close(self) -> None:
        """Close the session, exiting the internal thread."""
        self.stop_flag.set()
        self.thread.join()
