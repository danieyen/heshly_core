from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class RuleStatus(str, Enum):

    ACTIVE = "active"

    INACTIVE = "inactive"


@dataclass(slots=True)
class BusinessRule:

    rule_id: str

    tenant_id: str

    name: str

    condition: str

    action: str

    status: RuleStatus = RuleStatus.ACTIVE

    priority: int = 100

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )