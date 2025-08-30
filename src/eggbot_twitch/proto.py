from __future__ import annotations

import json
import secrets
import threading
import time

from werkzeug.serving import make_server
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

_AUTHO_TIMEOUT_SECONDS = 30

caught_request: Request | None = None


class RedirectCatcher(threading.Thread):

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.server = make_server(host, port, self.application, threaded=True)

    def run(self) -> None:
        self.server.serve_forever()

    @staticmethod
    @Request.application
    def application(request: Request) -> Response:
        global caught_request
        caught_request = request

        return Response("🥚")


def prompt_to_auth_url(
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    *,
    force_verify: bool = True,
) -> None:
    url = (
        "https://id.twitch.tv/oauth2/authorize?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
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
    timeout_at = time.time() + _AUTHO_TIMEOUT_SECONDS
    counter = ""
    while not caught_request:
        if counter != f"{int(timeout_at - time.time())}":
            counter = f"{int(timeout_at - time.time())}"
            print(f"\rTimeout in {counter:<10}", end="")

        if time.time() >= timeout_at:
            raise TimeoutError()


def main() -> int:
    catcher = RedirectCatcher(host="127.0.0.1", port=5005)

    prompt_to_auth_url(
        client_id="es76t05hv4zarhowki8wypjfa7yqd0",
        redirect_uri="http://localhost:5005/callback",
        scope="user:bot",
        state=secrets.token_urlsafe(64),
    )

    start_auth_catcher_thread(catcher)

    try:
        wait_for_auth(_AUTHO_TIMEOUT_SECONDS)

    except KeyboardInterrupt:
        print("\nUser cancelled operation.")
        return 1

    except TimeoutError:
        print("\nTimed out while waiting for user to authorize app.")
        return 1

    finally:
        stop_auth_catcher_thread(catcher)

    print(json.dumps(caught_request.__dict__, indent=2, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
