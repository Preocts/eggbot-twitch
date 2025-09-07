"""Custom Exceptions for the module."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True, slots=True)
class UnauthorizedError(Exception):
    status_code: int
    url: str
    error: str
    message: str

    def __str__(self) -> str:
        return f"({self.status_code}) {self.error}: {self.message}"
