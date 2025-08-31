"""Prototype."""

from __future__ import annotations

from .twitchauth import get_autho_code

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

    if autho is None:
        raise SystemExit(1)

    elif autho.error:
        print(f"Error: {autho.error} - {autho.error_description}")
        raise SystemExit(1)

    print("Authorization granted.")

    raise SystemExit(0)
