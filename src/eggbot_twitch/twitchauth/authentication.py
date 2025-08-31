from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True, slots=True)
class Authentication:
    """Represent the response of an authentication request"""
