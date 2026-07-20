from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import mean


class SalesForecasting:
    """
    Sales Forecasting

    Lightweight forecasting engine using historical revenue
    and weighted pipeline.

    Expected history format

    {
        "date": datetime(...),
        "revenue": 125000
    }

    Expected opportunity format

    {
        "value": 50000,
        "probability": 70,
        "status": "open"
    }
    """

    # =====================================================
    # Revenue Forecast
    # =====================================================

    def forecast_revenue(
        self,
        history: list[dict],
        periods: int = 6,
    ) -> dict:

        revenues = [

            float(item.get("revenue", 0))

            for item in history

        ]

        average = (
            mean(revenues)
            if revenues
            else 0.0
        )

        forecast = []

        start = datetime.now(UTC)

        for i in range(periods):

            forecast.append(

                {

                    "period": i + 1,

                    "date": (
                        start +
                        timedelta(days=30 * (i + 1))
                    ),

                    "forecast_revenue": round(
                        average,
                        2,
                    ),

                }

            )

        trend = "stable"

        if len(revenues) >= 2:

            if revenues[-1] > revenues[0]:
                trend = "upward"

            elif revenues[-1] < revenues[0]:
                trend = "downward"

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "historical_average": round(
                average,
                2,
            ),

            "trend": trend,

            "forecast": forecast,

        }

    # =====================================================
    # Weighted Pipeline Forecast
    # =====================================================

    def pipeline_forecast(
        self,
        opportunities: list[dict],
    ) -> dict:

        weighted = 0.0
        pipeline = 0.0

        for opportunity in opportunities:

            if (
                opportunity.get(
                    "status",
                    "open",
                ).lower()
                != "open"
            ):
                continue

            value = float(
                opportunity.get(
                    "value",
                    0,
                )
            )

            probability = float(
                opportunity.get(
                    "probability",
                    0,
                )
            )

            pipeline += value

            weighted += (
                value *
                probability /
                100
            )

        confidence = (
            round(
                weighted /
                pipeline *
                100,
                2,
            )
            if pipeline
            else 0.0
        )

        return {

            "pipeline_value": round(
                pipeline,
                2,
            ),

            "weighted_pipeline": round(
                weighted,
                2,
            ),

            "forecast_confidence": confidence,

        }

    # =====================================================
    # Combined Forecast
    # =====================================================

    def forecast(
        self,
        history: list[dict],
        opportunities: list[dict],
        periods: int = 6,
    ) -> dict:

        revenue = self.forecast_revenue(
            history,
            periods,
        )

        pipeline = self.pipeline_forecast(
            opportunities,
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "trend": revenue["trend"],

            "historical_average": revenue[
                "historical_average"
            ],

            "forecast": revenue[
                "forecast"
            ],

            "pipeline": pipeline,

        }

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        return {

            "trend": report[
                "trend"
            ],

            "historical_average": report[
                "historical_average"
            ],

            "pipeline_value": report[
                "pipeline"
            ][
                "pipeline_value"
            ],

            "weighted_pipeline": report[
                "pipeline"
            ][
                "weighted_pipeline"
            ],

            "forecast_confidence": report[
                "pipeline"
            ][
                "forecast_confidence"
            ],

            "forecast_periods": len(
                report[
                    "forecast"
                ]
            ),

        }