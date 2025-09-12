"""Custom Exceptions for the module."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True, slots=True)
class TwitchAPIError(Exception):
    """Base exception class for all Twitch API Errors."""

    status_code: int
    url: str
    error: str
    message: str

    def __str__(self) -> str:
        return f"({self.status_code}) {self.error}: {self.message}"


@dataclasses.dataclass(frozen=True, slots=True)
class BadRequestError(TwitchAPIError):
    """Represents any failed request response."""


@dataclasses.dataclass(frozen=True, slots=True)
class UnauthorizedError(TwitchAPIError):
    """Represents 401 Unauthorized request responses."""
