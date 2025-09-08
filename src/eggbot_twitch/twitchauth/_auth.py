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
    client_id: str

    @classmethod
    @abc.abstractmethod
    def parse_response(cls, response: dict[str, Any], client_id: str) -> Self: ...

    @classmethod
    def load(cls, fp: SupportsRead[bytes]) -> Self:
        """Load UserAuth from a file. Must be in JSON format."""
        contents = json.load(fp)
        client_id = contents.pop("client_id")
        return cls.parse_response(contents, client_id)

    def dump(self, fp: SupportsWrite[bytes]) -> None:
        """Save UserAuth to a file in JSON format."""
        fp.write(json.dumps(dataclasses.asdict(self)).encode())
