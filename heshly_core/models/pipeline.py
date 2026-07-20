from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class PipelineMetrics:

    pipeline_id: str

    total_opportunities: int = 0

    total_value: float = 0.0

    weighted_value: float = 0.0

    calculated_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class PipelineStageSummary:

    stage_id: str

    stage_name: str

    opportunity_count: int = 0

    total_value: float = 0.0

    probability: float = 0.0