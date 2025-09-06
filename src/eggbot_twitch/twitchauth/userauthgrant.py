from __future__ import annotations

import dataclasses
import urllib.parse


@dataclasses.dataclass(frozen=True, slots=True)
class UserAuthGrant:
    """Represent the response of a user authorization grant request."""

    state: str = ""
    redirect_url: str = ""
    code: str = ""
    scope: str = ""
    error: str = ""
    error_description: str = ""

    @classmethod
    def parse_url(cls, url: str) -> UserAuthGrant:
        """Create Authorization from callback url."""
        parts = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parts.query)

        return cls(
            state=query.get("state", [""])[0],
            redirect_url=f"{parts.scheme}://{parts.netloc}{parts.path}",
            code=query.get("code", [""])[0],
            scope=query.get("scope", [""])[0],
            error=query.get("error", [""])[0],
            error_description=query.get("error_description", [""])[0],
        )
