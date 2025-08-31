from __future__ import annotations

from .authentication import Authentication
from .authorization import Authorization


def get_authentication(authorization: Authorization) -> Authentication | None:
    """Get bearer authentication from a user authorization."""
    return Authentication()
