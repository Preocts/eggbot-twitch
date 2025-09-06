from __future__ import annotations

import abc
import dataclasses
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from typing import Self

    from _typeshed import SupportsRead
    from _typeshed import SupportsWrite


@dataclasses.dataclass(frozen=True, slots=True)
class Auth(abc.ABC):
    """Authorization token for TwitchTV."""

    access_token: str
    expires_in: int
    expires_at: int

    @classmethod
    @abc.abstractmethod
    def parse_response(cls, response: dict[str, Any]) -> Self: ...

    @classmethod
    def load(cls, fp: SupportsRead[bytes]) -> Self:
        """Load UserAuth from a file. Must be in JSON format."""
        return cls.parse_response(json.load(fp))

    def dump(self, fp: SupportsWrite[bytes]) -> None:
        """Save UserAuth to a file in JSON format."""
        fp.write(json.dumps(dataclasses.asdict(self)).encode())
