from __future__ import annotations

import json
import logging
import threading
import time

import websockets.sync.client

from ._session import Session

# TODO
# - capture exit signal sigkill, clean up all sessions

_INITIAL_MESSAGE_TIMEOUT_SECONDS = 10.0
_CONNECTION_TIMEOUT_SECONDS = _INITIAL_MESSAGE_TIMEOUT_SECONDS + 1
_MAX_CONNECTION_RETRIES = 3

logger = logging.getLogger("eventclient")


def get_session(uri: str) -> Session:
    """
    Start a EventSub Session, and return that session.

    Blocks until session is started.

    Args:
        uri (str): URI of the websocket server

    Raises:
        TimeoutError: If waiting for a session id exceeds _CONNECTION_TIMEOUT_SECONDS
        ConnectoinError: If the session could not be created
    """

    session = Session(uri, False)

    session.thread = threading.Thread(target=_session_thread, args=(session,))

    session.thread.start()

    timeout_at = time.time() + _CONNECTION_TIMEOUT_SECONDS
    while time.time() < timeout_at:
        if session.session_id:
            return session

        if session.exception is not None:
            session.close()
            msg = f"Failed to establish connection to websocket server after {_MAX_CONNECTION_RETRIES} retries. {session.exception}"
            raise ConnectionError(msg) from session.exception

        time.sleep(0.1)

    session.close()
    raise TimeoutError("Connection to session hit max timeout.")


def _session_thread(session: Session, retry_count: int = 0) -> None:
    """Internal: Session Thread."""
    session.active = True

    try:
        with websockets.sync.client.connect(session.uri) as websocket:

            # I'm assuming the first message will be the session_id
            # That's safe.... right?
            init_message = websocket.recv(timeout=_INITIAL_MESSAGE_TIMEOUT_SECONDS)
            _init_message = json.loads(init_message)

            session.session_id = _init_message["payload"]["session"]["id"]

            while not session.stop_flag.is_set():
                try:
                    message = websocket.recv(timeout=0.1, decode=True)

                except TimeoutError:
                    continue

                session.messages.put(message)

    except (ConnectionResetError, ConnectionRefusedError) as exc:
        if retry_count < _MAX_CONNECTION_RETRIES:
            backoff = 0.3 * retry_count
            logger.warning("Connection failed: Attempting reconnect in %s seconds", backoff)
            time.sleep(backoff)
            _session_thread(session, retry_count + 1)
        else:
            logger.error("Connection failed %s", exc)
            session.exception = exc

    finally:
        session.active = False
