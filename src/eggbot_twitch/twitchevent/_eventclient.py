from __future__ import annotations

import json
import threading
import time

import websockets.sync.client

from ._session import Session

# TODO
# - capture exit signal sigkill, clean up all sessions

_SESSIONS: dict[str, Session] = {}
_INITIAL_MESSAGE_TIMEOUT_SECONDS = 10.0
_CONNECTION_TIMEOUT_SECONDS = _INITIAL_MESSAGE_TIMEOUT_SECONDS + 1
_MAX_CONNECTION_RETRIES = 3


def start_session_thread(host: str, port: int | None) -> str:
    """
    Start a EventSub Session, returns session id needed to get message queue

    Blocks until session is started. If None is returned, the session failed
    to start and was dropped.

    Args:
        host (str): Host name of the websocket endpoint
        port (int | None): Port to use. Defaults to 80 (ws://) or 443 (wss://)

    Raises:
        TimeoutError: If waiting for a session id exceeds _CONNECTION_TIMEOUT_SECONDS
    """
    port = port if port is not None else 80 if host.startswith("ws://") else 443

    session = Session(host, port, False)

    session.thread = threading.Thread(target=_session_thread, args=(session,))

    session.thread.start()

    timeout_at = time.time() + _CONNECTION_TIMEOUT_SECONDS
    while time.time() < timeout_at:
        if session.session_id:
            _SESSIONS[session.session_id] = session
            return session.session_id

        if session.exception is not None:
            msg = f"Failed to establish connection to websocket server after {_MAX_CONNECTION_RETRIES} retries. {session.exception}"
            raise ConnectionError(msg) from session.exception

        time.sleep(0.1)

    raise TimeoutError("Connection to session hit max timeout.")


def _session_thread(session: Session, retry_count: int = 0) -> None:
    """Internal: Session Thread."""
    session.active = True

    try:
        with websockets.sync.client.connect(f"{session.host}:{session.port}") as websocket:

            # I'm assuming the first message will be the session_id
            # That's safe.... right?
            init_message = websocket.recv(timeout=_INITIAL_MESSAGE_TIMEOUT_SECONDS)
            _init_message = json.loads(init_message)

            session.session_id = _init_message["payload"]["session"]["id"]

    except (ConnectionResetError, ConnectionRefusedError) as exc:
        if retry_count < _MAX_CONNECTION_RETRIES:
            time.sleep(0.3 * retry_count)
            _session_thread(session, retry_count + 1)
        else:
            session.exception = exc

    finally:
        session.active = False


def end_session_thread(session_id: str | None) -> None:
    """Closes given session thread. If None is given, closes all open threads."""
    for session in _SESSIONS.values():
        if session_id is None or session_id == session.session_id:
            session.stop_flag.set()
            session.thread.join()
