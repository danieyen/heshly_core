from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


# ==========================================================
# Metric Types
# ==========================================================

class MetricType(str, Enum):

    COUNT = "count"

    SUM = "sum"

    AVERAGE = "average"

    PERCENTAGE = "percentage"

    RATIO = "ratio"

    CURRENCY = "currency"

    DURATION = "duration"

    SCORE = "score"


# ==========================================================
# Time Periods
# ==========================================================

class TimePeriod(str, Enum):

    TODAY = "today"

    YESTERDAY = "yesterday"

    WEEK = "week"

    MONTH = "month"

    QUARTER = "quarter"

    YEAR = "year"

    CUSTOM = "custom"


# ==========================================================
# Dashboard Types
# ==========================================================

class DashboardType(str, Enum):

    EXECUTIVE = "executive"

    SALES = "sales"

    CRM = "crm"

    APPOINTMENTS = "appointments"

    CUSTOMERS = "customers"

    AI = "ai"

    MARKETING = "marketing"

    OPERATIONS = "operations"


# ==========================================================
# Metric
# ==========================================================

@dataclass(slots=True)
class Metric:

    metric_id: str

    name: str

    metric_type: MetricType

    value: float = 0.0

    unit: str = ""

    description: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ==========================================================
# KPI
# ==========================================================

@dataclass(slots=True)
class KPI:

    kpi_id: str

    name: str

    value: float

    target: float = 0.0

    unit: str = ""

    trend: float = 0.0

    period: TimePeriod = TimePeriod.MONTH

    description: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Analytics Filter
# ==========================================================

@dataclass(slots=True)
class AnalyticsFilter:

    business_id: str | None = None

    customer_id: str | None = None

    employee_id: str | None = None

    service_id: str | None = None

    lead_id: str | None = None

    opportunity_id: str | None = None

    period: TimePeriod = TimePeriod.MONTH

    start_date: datetime | None = None

    end_date: datetime | None = None


# ==========================================================
# Chart Data
# ==========================================================

@dataclass(slots=True)
class ChartSeries:

    name: str

    labels: list[str] = field(
        default_factory=list
    )

    values: list[float] = field(
        default_factory=list
    )


# ==========================================================
# Dashboard Widget
# ==========================================================

@dataclass(slots=True)
class DashboardWidget:

    widget_id: str

    title: str

    widget_type: str

    data: Any = None

    width: int = 6

    height: int = 4

    position: int = 0


# ==========================================================
# Dashboard
# ==========================================================

@dataclass(slots=True)
class Dashboard:

    dashboard_id: str

    name: str

    dashboard_type: DashboardType

    widgets: list[DashboardWidget] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def add_widget(
        self,
        widget: DashboardWidget,
    ):

        self.widgets.append(widget)

        self.updated_at = datetime.now(UTC)

    @property
    def widget_count(self) -> int:

        return len(self.widgets)


# ==========================================================
# Analytics Snapshot
# ==========================================================

@dataclass(slots=True)
class AnalyticsSnapshot:

    snapshot_id: str

    business_id: str

    period: TimePeriod

    metrics: list[Metric] = field(
        default_factory=list
    )

    kpis: list[KPI] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def add_metric(
        self,
        metric: Metric,
    ):

        self.metrics.append(metric)

    def add_kpi(
        self,
        kpi: KPI,
    ):

        self.kpis.append(kpi)

    @property
    def metric_count(self):

        return len(self.metrics)

    @property
    def kpi_count(self):

        return len(self.kpis)