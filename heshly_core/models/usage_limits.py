from __future__ import annotations

from dataclasses import dataclass

from heshly_core.models.usage import (
    UsageMetric,
)


@dataclass(slots=True)
class UsageLimit:
    """
    Defines allowed usage for a metric.
    """

    metric: UsageMetric

    limit: int | None

    # None means unlimited


    def is_unlimited(self) -> bool:

        return self.limit is None