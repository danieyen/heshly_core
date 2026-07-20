from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RateLimitRule:
    """
    Defines API request limits.
    """

    name: str

    requests: int

    window_seconds: int = 60