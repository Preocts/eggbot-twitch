from __future__ import annotations

import secrets
import threading
import time
import urllib.parse
import logging

from werkzeug.serving import make_server
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from .userauthgrant import UserAuthGrant

_AUTHO_TIMEOUT_SECONDS = 30

logger = logging.getLogger("twitchauth")
_caught_autho_request: Request | None = None


class RedirectCatcher(threading.Thread):

    def __init__(self, host: str, port: int) -> None:
        """Create a server within a thread."""
        super().__init__()
        self.server = make_server(host, port, self.application, threaded=True)

    def run(self) -> None:
        """Run the server forever."""
        self.server.serve_forever()

    @staticmethod
    @Request.application
    def application(request: Request) -> Response:
        """Handle requests to the server."""
        global _caught_autho_request
        _caught_autho_request = request

        return Response("🥚")


def prompt_to_auth_url(
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    *,
    force_verify: bool = True,
) -> None:
    """Print a prompt to the stdout for the user to follow."""
    url = (
        "https://id.twitch.tv/oauth2/authorize"
        "?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={urllib.parse.quote(scope)}"
        f"&state={state}"
        f"&force_verify={str(force_verify).lower()}"
    )
    print("Open the following url in your browser to authorize this app with Twitch:")
    print(url)


def start_auth_catcher_thread(auth_catcher: RedirectCatcher) -> None:
    """Start the thread containing the werkzeug webserver."""
    logger.info("Starting emphemeral webserver to capture auth request.")
    auth_catcher.start()


def stop_auth_catcher_thread(auth_catcher: RedirectCatcher) -> None:
    """Stop the thread containing the wekzeug webserver, block until closed."""
    logger.info("Stopping webserver...")
    auth_catcher.server.shutdown()
    auth_catcher.join()
    logger.info("Webserver stopped.")


def wait_for_auth(timeout_seconds: int) -> None:
    """Wait for the global 'caught_request' to be populated or until timeout expires."""
    timeout_at = time.time() + timeout_seconds
    counter = ""
    while not _caught_autho_request:
        if counter != f"{int(timeout_at - time.time())}":
            counter = f"{int(timeout_at - time.time())}"
            print(f"\rTimeout in {counter:<10}", end="")

        if time.time() >= timeout_at:
            raise TimeoutError()


def get_user_grant(
    callback_host: str,
    callback_port: int,
    twitch_app_client_id: str,
    redirect_url: str,
    scope: str,
    timeout: int = _AUTHO_TIMEOUT_SECONDS,
) -> UserAuthGrant | None:
    """
    Request user authorization code.

    This requires the user to open a generated link, accept the authorizatoin request,
    and for the redirect to be captured by a local webserver.

    A small werkzeug server is spun up in a thread during this operation.

    The operation will timeout, failing, in _AUTHO_TIMEOUT_SECONDS.

    Args:
        callback_host: Host name of the HTTP service setup to catch redirect (usually 'localhost')
        callback_port: Port of HTTP service setup to catch redirect
        twitch_app_client_id: The registered Twitch app id
        redirect_url: The registered redirect url of the Twitch app
        scope: Space delimited list of scope to request
        timeout: After timeout expires, return failure (None)
    """
    global _caught_autho_request

    catcher = RedirectCatcher(host=callback_host, port=callback_port)
    caught_url = ""
    state = secrets.token_urlsafe(64)

    prompt_to_auth_url(
        client_id=twitch_app_client_id,
        redirect_uri=redirect_url,
        scope=scope,
        state=state,
    )

    start_auth_catcher_thread(catcher)

    try:
        wait_for_auth(timeout)

    except KeyboardInterrupt:  # pragma: no cover
        logger.error("User cancelled operation.")
        return None

    except TimeoutError:
        logger.error("Timed out while waiting for user to authorize app.")
        return None

    finally:
        if _caught_autho_request is not None:
            caught_url = _caught_autho_request.url
            _caught_autho_request = None

        stop_auth_catcher_thread(catcher)

    autho = UserAuthGrant.parse_url(caught_url)

    if autho.state != state:
        logger.error("State mismatch, cannot trust source.")
        return None

    print("\n")

    return autho
