from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# ==========================================================
# BI Dashboard Types
# ==========================================================

class BIDashboardType(str, Enum):

    EXECUTIVE = "executive"

    SALES = "sales"

    FINANCE = "finance"

    OPERATIONS = "operations"

    MARKETING = "marketing"

    CRM = "crm"

    APPOINTMENTS = "appointments"

    AI = "ai"

    CUSTOM = "custom"


# ==========================================================
# BI Widget
# ==========================================================

class BIWidgetType(str, Enum):

    KPI = "kpi"

    CHART = "chart"

    TABLE = "table"

    PIE = "pie"

    BAR = "bar"

    LINE = "line"

    AREA = "area"

    GAUGE = "gauge"

    MAP = "map"


# ==========================================================
# Widget Model
# ==========================================================

@dataclass(slots=True)
class BIWidget:

    widget_id: str

    title: str

    widget_type: BIWidgetType

    data_source: str

    query: str = ""

    configuration: dict = field(
        default_factory=dict
    )

    refresh_interval: int = 300

    enabled: bool = True


# ==========================================================
# Dashboard Model
# ==========================================================

@dataclass(slots=True)
class BIDashboard:

    dashboard_id: str

    business_id: str

    name: str

    dashboard_type: BIDashboardType

    widgets: list[BIWidget] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# KPI Model
# ==========================================================

@dataclass(slots=True)
class BIKPI:

    name: str

    value: float

    target: float | None = None

    unit: str = ""

    trend: float = 0.0

    status: str = "normal"

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Insight Model
# ==========================================================

@dataclass(slots=True)
class BIInsight:

    insight_id: str

    title: str

    description: str

    severity: str = "info"

    category: str = "general"

    confidence: float = 1.0

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Forecast Model
# ==========================================================

@dataclass(slots=True)
class BIForecast:

    forecast_id: str

    metric: str

    horizon_days: int

    predicted_value: float

    confidence: float

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Benchmark Model
# ==========================================================

@dataclass(slots=True)
class BIBenchmark:

    metric: str

    current_value: float

    benchmark_value: float

    variance: float

    percentage_variance: float


# ==========================================================
# BI Report
# ==========================================================

@dataclass(slots=True)
class BIReport:

    report_id: str

    business_id: str

    dashboards: list[BIDashboard] = field(
        default_factory=list
    )

    kpis: list[BIKPI] = field(
        default_factory=list
    )

    insights: list[BIInsight] = field(
        default_factory=list
    )

    forecasts: list[BIForecast] = field(
        default_factory=list
    )

    benchmarks: list[BIBenchmark] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )