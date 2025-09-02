"""Prototype."""

from __future__ import annotations

from eggviron import Eggviron
from eggviron import EnvFileLoader

from .twitchauth import get_user_authorization
from .twitchauth import get_user_grant

if __name__ == "__main__":
    try:
        environ = Eggviron().load(EnvFileLoader())

    except FileNotFoundError:
        print("Copy '.env_sample' to '.env' and fill in the needed secrets.")
        raise SystemExit(1)

    # TODO: Move to config or .env file
    callback_host = "localhost"
    callback_port = 5005
    twitch_app_client_id = "es76t05hv4zarhowki8wypjfa7yqd0"
    twitch_app_client_secret = environ["TWITCH_APP_CLIENT_SECRET"]
    redirect_url = "http://localhost:5005/callback"
    scope = "user:read:chat user:read:email"

    autho = get_user_grant(
        callback_host=callback_host,
        callback_port=callback_port,
        twitch_app_client_id=twitch_app_client_id,
        redirect_url=redirect_url,
        scope=scope,
    )

    if autho is None:
        raise SystemExit(1)

    elif autho.error:
        print(f"Error: {autho.error} - {autho.error_description}")
        raise SystemExit(1)

    print("Authorization granted.")

    authe = get_user_authorization(
        twitch_app_client_id=twitch_app_client_id,
        twitch_app_client_secret=twitch_app_client_secret,
        redirect_url=redirect_url,
        userauthgrant=autho,
    )

    if authe is None:
        raise SystemExit(1)

    print("Authentication granted.")
    print(authe)

    raise SystemExit(0)
