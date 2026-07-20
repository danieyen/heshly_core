from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# ==========================================================
# Dashboard Types
# ==========================================================

class DashboardType(str, Enum):

    EXECUTIVE = "executive"

    SALES = "sales"

    CRM = "crm"

    APPOINTMENTS = "appointments"

    CUSTOMERS = "customers"

    MARKETING = "marketing"

    AI = "ai"

    OPERATIONS = "operations"

    CUSTOM = "custom"


# ==========================================================
# Widget Types
# ==========================================================

class WidgetType(str, Enum):

    KPI = "kpi"

    METRIC = "metric"

    LINE_CHART = "line_chart"

    BAR_CHART = "bar_chart"

    PIE_CHART = "pie_chart"

    DONUT_CHART = "donut_chart"

    AREA_CHART = "area_chart"

    TABLE = "table"

    LIST = "list"

    GAUGE = "gauge"

    PROGRESS = "progress"

    TEXT = "text"

    NUMBER = "number"


# ==========================================================
# Dashboard Layout
# ==========================================================

class DashboardLayout(str, Enum):

    GRID = "grid"

    RESPONSIVE = "responsive"

    FREE = "free"


# ==========================================================
# Widget Size
# ==========================================================

@dataclass(slots=True)
class WidgetSize:

    width: int = 6

    height: int = 4


# ==========================================================
# Widget Position
# ==========================================================

@dataclass(slots=True)
class WidgetPosition:

    row: int = 0

    column: int = 0


# ==========================================================
# Dashboard Widget
# ==========================================================

@dataclass(slots=True)
class DashboardWidget:

    widget_id: str

    title: str

    widget_type: WidgetType

    data: Any = None

    subtitle: str = ""

    icon: str = ""

    color: str = ""

    size: WidgetSize = field(
        default_factory=WidgetSize
    )

    position: WidgetPosition = field(
        default_factory=WidgetPosition
    )

    visible: bool = True

    refresh_seconds: int = 300

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ==========================================================
# Dashboard Section
# ==========================================================

@dataclass(slots=True)
class DashboardSection:

    section_id: str

    title: str

    widgets: list[DashboardWidget] = field(
        default_factory=list
    )

    collapsed: bool = False

    def add_widget(
        self,
        widget: DashboardWidget,
    ):

        self.widgets.append(widget)

    @property
    def widget_count(self):

        return len(self.widgets)


# ==========================================================
# Dashboard
# ==========================================================

@dataclass(slots=True)
class Dashboard:

    dashboard_id: str

    name: str

    dashboard_type: DashboardType

    layout: DashboardLayout = DashboardLayout.GRID

    sections: list[DashboardSection] = field(
        default_factory=list
    )

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

    def add_section(
        self,
        section: DashboardSection,
    ):

        self.sections.append(section)

        self.updated_at = datetime.now(UTC)

    @property
    def section_count(self):

        return len(self.sections)

    @property
    def widget_count(self):

        return sum(

            section.widget_count

            for section in self.sections

        )


# ==========================================================
# Dashboard Snapshot
# ==========================================================

@dataclass(slots=True)
class DashboardSnapshot:

    snapshot_id: str

    dashboard_id: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    widgets: list[DashboardWidget] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def add_widget(
        self,
        widget: DashboardWidget,
    ):

        self.widgets.append(widget)

    @property
    def widget_count(self):

        return len(self.widgets)