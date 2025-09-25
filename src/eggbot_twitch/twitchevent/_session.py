from __future__ import annotations

import dataclasses
import queue
import threading
from collections.abc import Iterator


@dataclasses.dataclass
class Session:
    """Represents a webscocket session."""

    uri: str
    active: bool
    session_id: str = ""
    messages: queue.Queue[str] = dataclasses.field(default_factory=queue.Queue)
    thread: threading.Thread = dataclasses.field(default_factory=threading.Thread)
    stop_flag: threading.Event = dataclasses.field(default_factory=threading.Event)
    exception: Exception | None = None

    def close(self) -> None:
        """Close the session, exiting the internal thread."""
        self.stop_flag.set()
        self.thread.join()

    def message_iter(self, max_poll_count: int = 10, poll_timeout: float = 0.1) -> Iterator[str]:
        """Iterator that returns up to max_poll_count messages from queue."""
        for _ in range(max_poll_count):
            try:
                yield self.messages.get(timeout=poll_timeout)

            except queue.Empty:
                continue
