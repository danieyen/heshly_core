from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional


class OpportunityPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class OpportunityActivityType(str, Enum):
    CREATED = "created"
    STAGE_CHANGED = "stage_changed"
    VALUE_UPDATED = "value_updated"
    WON = "won"
    LOST = "lost"


@dataclass(slots=True)
class OpportunityStageChange:
    opportunity_id: str

    previous_stage: Optional[str]

    new_stage: str

    changed_by: Optional[str] = None

    changed_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class OpportunityValueUpdate:
    opportunity_id: str

    previous_value: float

    new_value: float

    updated_by: Optional[str] = None

    updated_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class OpportunityActivity:
    activity_id: str

    opportunity_id: str

    activity_type: OpportunityActivityType

    description: str

    created_by: Optional[str] = None

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class OpportunityForecast:
    opportunity_id: str

    expected_value: float

    probability: float

    forecast_value: float = 0.0

    calculated_at: datetime = field(
        default_factory=datetime.utcnow
    )

    def calculate(self):

        self.forecast_value = (
            self.expected_value *
            self.probability
        )

        return self.forecast_value


@dataclass(slots=True)
class OpportunityFilter:
    pipeline_id: Optional[str] = None

    stage_id: Optional[str] = None

    status: Optional[str] = None

    owner: Optional[str] = None

    min_value: Optional[float] = None

    max_value: Optional[float] = None

    close_before: Optional[date] = None

    close_after: Optional[date] = None