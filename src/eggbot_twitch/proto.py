"""Prototype."""

from __future__ import annotations

from eggviron import Eggviron
from eggviron import EnvFileLoader

from .twitchauth import get_authorization
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

    user_greant = get_user_grant(
        callback_host=callback_host,
        callback_port=callback_port,
        twitch_app_client_id=twitch_app_client_id,
        redirect_url=redirect_url,
        scope=scope,
    )

    if user_greant is None:
        raise SystemExit(1)

    elif user_greant.error:
        print(f"Error: {user_greant.error} - {user_greant.error_description}")
        raise SystemExit(1)

    print("Authorization granted.")

    user_auth = get_authorization(
        twitch_app_client_id=twitch_app_client_id,
        twitch_app_client_secret=twitch_app_client_secret,
        user_auth=user_greant,
    )

    refresh_auth = get_authorization(
        twitch_app_client_id=twitch_app_client_id,
        twitch_app_client_secret=twitch_app_client_secret,
        user_auth=user_auth,
    )

    client_auth = get_authorization(
        twitch_app_client_id=twitch_app_client_id,
        twitch_app_client_secret=twitch_app_client_secret,
    )

    if user_auth is None:
        print("Failed to get User Auth")
        raise SystemExit(1)

    if refresh_auth is None:
        print("Failed to get Refresh Auth")
        raise SystemExit(1)

    if client_auth is None:
        print("Failed to get Client Auth")
        raise SystemExit(1)

    print("Authentication granted.")

    raise SystemExit(0)
