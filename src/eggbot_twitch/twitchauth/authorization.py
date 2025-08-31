from __future__ import annotations

import dataclasses
import urllib.parse


@dataclasses.dataclass(frozen=True, slots=True)
class Authorization:
    """Represent the response of an authorizatoin request."""

    state: str = ""
    code: str = ""
    scope: str = ""
    error: str = ""
    error_description: str = ""

    @classmethod
    def parse_url(cls, url: str) -> Authorization:
        """Create Authorization from callback url."""
        parts = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parts.query)

        return cls(
            state=query.get("state", [""])[0],
            code=query.get("code", [""])[0],
            scope=query.get("scope", [""])[0],
            error=query.get("error", [""])[0],
            error_description=query.get("error_description", [""])[0],
        )
