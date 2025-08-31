from __future__ import annotations

import secrets
import threading
import time
import urllib.parse

from werkzeug.serving import make_server
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from .authorization import Authorization

_AUTHO_TIMEOUT_SECONDS = 30

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
    auth_catcher.start()


def stop_auth_catcher_thread(auth_catcher: RedirectCatcher) -> None:
    """Stop the thread containing the wekzeug webserver, block until closed."""
    auth_catcher.server.shutdown()
    auth_catcher.join()


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


def get_autho_code(
    callback_host: str,
    callback_port: int,
    twitch_app_client_id: str,
    redirect_url: str,
    scope: str,
    timeout: int = _AUTHO_TIMEOUT_SECONDS,
) -> Authorization | None:
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
        print("\nError: User cancelled operation.")
        return None

    except TimeoutError:
        print("\nError: Timed out while waiting for user to authorize app.")
        return None

    finally:
        if _caught_autho_request is not None:
            caught_url = _caught_autho_request.url
            _caught_autho_request = None

        stop_auth_catcher_thread(catcher)

    autho = Authorization.parse_url(caught_url)

    if autho.state != state:
        print("\nError: State mismatch, cannot trust source.")
        return None

    print("\nSuccess: Authorization obtained.")

    return autho


if __name__ == "__main__":
    # TODO: Move to config or .env file
    callback_host = "localhost"
    callback_port = 5005
    twitch_app_client_id = "es76t05hv4zarhowki8wypjfa7yqd0"
    redirect_url = "http://localhost:5005/callback"
    scope = "user:read:chat user:read:email"

    autho = get_autho_code(
        callback_host=callback_host,
        callback_port=callback_port,
        twitch_app_client_id=twitch_app_client_id,
        redirect_url=redirect_url,
        scope=scope,
    )
    raise SystemExit(int(autho is None))
