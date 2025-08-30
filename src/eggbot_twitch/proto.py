from __future__ import annotations

import json
import secrets
import threading
from typing import TYPE_CHECKING

from werkzeug.serving import make_server
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

if TYPE_CHECKING:
    from _typeshed.wsgi import WSGIApplication

caught_request: Request | None = None


class RedirectCatcher(threading.Thread):

    def __init__(self, application: WSGIApplication) -> None:
        super().__init__()
        self.server = make_server("127.0.0.1", 5005, application, threaded=True)

    def run(self) -> None:
        self.server.serve_forever()


@Request.application
def application(request: Request) -> Response:
    global caught_request
    caught_request = request

    return Response("Caught the request, you can close this window now.")


def direct_to_auth_url(
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
    print("Open the following url in your browswer to authorize this app with Twitch:")
    print(url)


def main() -> int:
    catcher = RedirectCatcher(application)

    direct_to_auth_url(
        client_id="es76t05hv4zarhowki8wypjfa7yqd0",
        redirect_uri="http://localhost:5005/callback",
        scope="user:bot",
        state=secrets.token_urlsafe(64),
    )

    try:
        print("Waiting for user auth...")
        catcher.start()

        while not caught_request:
            ...

    except KeyboardInterrupt:
        return 1

    print("Shutting down catcher...")
    catcher.server.shutdown()
    catcher.join()

    print(json.dumps(caught_request.__dict__, indent=2, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
