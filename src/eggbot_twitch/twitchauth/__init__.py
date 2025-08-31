from __future__ import annotations

from ._twitch_authe import get_authentication
from ._twitch_autho import get_authorization
from .authentication import Authentication
from .authorization import Authorization

__all__ = [
    "Authentication",
    "Authorization",
    "get_authentication",
    "get_authorization",
]
