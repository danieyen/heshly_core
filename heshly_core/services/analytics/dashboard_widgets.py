from __future__ import annotations

from heshly_core.models.dashboard import (
    DashboardWidget,
    WidgetPosition,
    WidgetSize,
    WidgetType,
)


class DashboardWidgets:
    """
    Dashboard Widget Factory.

    Creates standardized widgets for the Business Dashboard.

    Supported widgets

        • KPI
        • Metric
        • Number
        • Progress
        • Gauge
        • Line Chart
        • Bar Chart
        • Pie Chart
        • Donut Chart
        • Area Chart
        • Table
        • List
        • Text
    """

    def __init__(self):

        self._counter = 1

    # =====================================================
    # Internal Helpers
    # =====================================================

    def _next_id(self) -> str:

        widget_id = f"WIDGET-{self._counter:05d}"

        self._counter += 1

        return widget_id

    def _create(
        self,
        title: str,
        widget_type: WidgetType,
        data=None,
        subtitle: str = "",
        icon: str = "",
        color: str = "",
        width: int = 6,
        height: int = 4,
    ) -> DashboardWidget:

        return DashboardWidget(

            widget_id=self._next_id(),

            title=title,

            widget_type=widget_type,

            data=data,

            subtitle=subtitle,

            icon=icon,

            color=color,

            size=WidgetSize(

                width=width,

                height=height,

            ),

            position=WidgetPosition(),

        )

    # =====================================================
    # KPI Widgets
    # =====================================================

    def kpi(
        self,
        title: str,
        value,
        subtitle: str = "",
    ):

        return self._create(

            title=title,

            widget_type=WidgetType.KPI,

            data=value,

            subtitle=subtitle,

        )

    def metric(
        self,
        title: str,
        value,
        subtitle: str = "",
    ):

        return self._create(

            title,

            WidgetType.METRIC,

            value,

            subtitle,

        )

    def number(
        self,
        title: str,
        value,
    ):

        return self._create(

            title,

            WidgetType.NUMBER,

            value,

        )

    def progress(
        self,
        title: str,
        percent: float,
    ):

        return self._create(

            title,

            WidgetType.PROGRESS,

            percent,

        )

    def gauge(
        self,
        title: str,
        value: float,
    ):

        return self._create(

            title,

            WidgetType.GAUGE,

            value,

        )

    # =====================================================
    # Chart Widgets
    # =====================================================

    def line_chart(
        self,
        title: str,
        series,
    ):

        return self._create(

            title,

            WidgetType.LINE_CHART,

            series,

            width=12,

            height=5,

        )

    def bar_chart(
        self,
        title: str,
        series,
    ):

        return self._create(

            title,

            WidgetType.BAR_CHART,

            series,

            width=12,

            height=5,

        )

    def pie_chart(
        self,
        title: str,
        series,
    ):

        return self._create(

            title,

            WidgetType.PIE_CHART,

            series,

            width=6,

            height=5,

        )

    def donut_chart(
        self,
        title: str,
        series,
    ):

        return self._create(

            title,

            WidgetType.DONUT_CHART,

            series,

            width=6,

            height=5,

        )

    def area_chart(
        self,
        title: str,
        series,
    ):

        return self._create(

            title,

            WidgetType.AREA_CHART,

            series,

            width=12,

            height=5,

        )

    # =====================================================
    # Data Widgets
    # =====================================================

    def table(
        self,
        title: str,
        rows,
    ):

        return self._create(

            title,

            WidgetType.TABLE,

            rows,

            width=12,

            height=6,

        )

    def list_widget(
        self,
        title: str,
        items,
    ):

        return self._create(

            title,

            WidgetType.LIST,

            items,

        )

    def text(
        self,
        title: str,
        text: str,
    ):

        return self._create(

            title,

            WidgetType.TEXT,

            text,

        )

    # =====================================================
    # Utilities
    # =====================================================

    def summary(
        self,
        widgets: list[DashboardWidget],
    ) -> dict:

        breakdown = {}

        for widget in widgets:

            key = widget.widget_type.value

            breakdown[key] = (

                breakdown.get(key, 0) + 1

            )

        return {

            "total_widgets": len(widgets),

            "widget_breakdown": breakdown,

        }