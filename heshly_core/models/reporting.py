from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# ==========================================================
# Report Types
# ==========================================================

class ReportType(str, Enum):

    ANALYTICS = "analytics"

    DASHBOARD = "dashboard"

    APPOINTMENTS = "appointments"

    CUSTOMERS = "customers"

    SALES = "sales"

    CRM = "crm"

    MARKETING = "marketing"

    AI = "ai"

    FINANCIAL = "financial"

    CUSTOM = "custom"


# ==========================================================
# Report Format
# ==========================================================

class ReportFormat(str, Enum):

    JSON = "json"

    CSV = "csv"

    XLSX = "xlsx"

    PDF = "pdf"

    HTML = "html"


# ==========================================================
# Report Status
# ==========================================================

class ReportStatus(str, Enum):

    PENDING = "pending"

    RUNNING = "running"

    COMPLETED = "completed"

    FAILED = "failed"


# ==========================================================
# Report Period
# ==========================================================

class ReportPeriod(str, Enum):

    TODAY = "today"

    WEEK = "week"

    MONTH = "month"

    QUARTER = "quarter"

    YEAR = "year"

    CUSTOM = "custom"


# ==========================================================
# Report Filter
# ==========================================================

@dataclass(slots=True)
class ReportFilter:

    field: str

    operator: str

    value: object


# ==========================================================
# Report Request
# ==========================================================

@dataclass(slots=True)
class ReportRequest:

    report_id: str

    business_id: str

    report_type: ReportType

    period: ReportPeriod = ReportPeriod.MONTH

    output_format: ReportFormat = ReportFormat.JSON

    status: ReportStatus = ReportStatus.PENDING

    filters: list[ReportFilter] = field(
        default_factory=list
    )

    parameters: dict = field(
        default_factory=dict
    )

    requested_by: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Report Result
# ==========================================================

@dataclass(slots=True)
class ReportResult:

    report_id: str

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    status: ReportStatus = ReportStatus.COMPLETED

    rows: int = 0

    execution_time_ms: float = 0.0

    data: dict = field(
        default_factory=dict
    )

    metadata: dict = field(
        default_factory=dict
    )


# ==========================================================
# Scheduled Report
# ==========================================================

@dataclass(slots=True)
class ScheduledReport:

    schedule_id: str

    report_request: ReportRequest

    enabled: bool = True

    cron: str = "0 8 * * *"

    last_run: datetime | None = None

    next_run: datetime | None = None


# ==========================================================
# Report Export
# ==========================================================

@dataclass(slots=True)
class ReportExport:

    export_id: str

    report_id: str

    format: ReportFormat

    filename: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    file_size: int = 0

    download_url: str = ""