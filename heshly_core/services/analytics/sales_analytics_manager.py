from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.sales_analytics import (
    SalesAnalyticsPeriod,
)
from heshly_core.services.analytics.revenue_analytics import (
    RevenueAnalytics,
)
from heshly_core.services.analytics.pipeline_analytics import (
    PipelineAnalytics,
)
from heshly_core.services.analytics.conversion_analytics import (
    ConversionAnalytics,
)
from heshly_core.services.analytics.win_loss_analysis import (
    WinLossAnalysis,
)
from heshly_core.services.analytics.sales_forecasting import (
    SalesForecasting,
)


class SalesAnalyticsManager:
    """
    Sales Analytics Manager

    Coordinates all sales analytics modules.

    Modules
    -------
    • Revenue Analytics
    • Pipeline Analytics
    • Conversion Analytics
    • Win/Loss Analysis
    • Sales Forecasting
    """

    def __init__(self):

        self.revenue = RevenueAnalytics()

        self.pipeline = PipelineAnalytics()

        self.conversion = ConversionAnalytics()

        self.win_loss = WinLossAnalysis()

        self.forecasting = SalesForecasting()

    # =====================================================
    # Individual Analytics
    # =====================================================

    def revenue_report(
        self,
        sales: list[dict],
    ):

        return self.revenue.analyze(sales)

    def pipeline_report(
        self,
        opportunities: list[dict],
    ):

        return self.pipeline.analyze(opportunities)

    def conversion_report(
        self,
        opportunities: list[dict],
    ):

        return self.conversion.analyze(opportunities)

    def win_loss_report(
        self,
        opportunities: list[dict],
    ):

        return self.win_loss.analyze(opportunities)

    def forecast_report(
        self,
        history: list[dict],
        opportunities: list[dict],
        periods: int = 6,
    ):

        return self.forecasting.forecast(
            history,
            opportunities,
            periods,
        )

    # =====================================================
    # Complete Report
    # =====================================================

    def complete_report(
        self,
        business_id: str,
        sales: list[dict],
        opportunities: list[dict],
        history: list[dict],
        period: SalesAnalyticsPeriod = (
            SalesAnalyticsPeriod.MONTHLY
        ),
    ) -> dict:

        revenue = self.revenue_report(
            sales
        )

        pipeline = self.pipeline_report(
            opportunities
        )

        conversion = self.conversion_report(
            opportunities
        )

        win_loss = self.win_loss_report(
            opportunities
        )

        forecast = self.forecast_report(
            history,
            opportunities,
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "business_id": business_id,

            "period": period.value,

            "revenue": revenue,

            "pipeline": pipeline,

            "conversion": conversion,

            "win_loss": win_loss,

            "forecast": forecast,

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "status": "healthy",

            "modules": {

                "revenue_analytics": True,

                "pipeline_analytics": True,

                "conversion_analytics": True,

                "win_loss_analysis": True,

                "sales_forecasting": True,

            },

        }

    # =====================================================
    # Executive Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        revenue = report["revenue"]

        pipeline = report["pipeline"]

        conversion = report["conversion"]

        win_loss = report["win_loss"]

        forecast = report["forecast"]

        return {

            "business_id": report[
                "business_id"
            ],

            "period": report[
                "period"
            ],

            "sales": revenue[
                "total_sales"
            ],

            "net_revenue": revenue[
                "net_revenue"
            ],

            "average_sale": revenue[
                "average_sale"
            ],

            "pipeline_value": pipeline[
                "pipeline_value"
            ],

            "weighted_pipeline": pipeline[
                "weighted_pipeline"
            ],

            "overall_conversion_rate": conversion[
                "overall_conversion_rate"
            ],

            "win_rate": win_loss[
                "win_rate"
            ],

            "loss_rate": win_loss[
                "loss_rate"
            ],

            "forecast_trend": forecast[
                "trend"
            ],

            "forecast_confidence": forecast[
                "pipeline"
            ][
                "forecast_confidence"
            ],

            "health": self.health(),

        }