from __future__ import annotations

from ._twitch_autho import get_authorization
from .authorization import Authorization

__all__ = [
    "Authorization",
    "get_authorization",
]
