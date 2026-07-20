from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import mean


class AppointmentForecasting:
    """
    Appointment Forecasting

    Forecasts future appointment demand using a simple
    moving-average model.

    Expected history format:

    [
        {
            "date": datetime(...),
            "appointments": 25
        },
        ...
    ]
    """

    # =====================================================
    # Forecast
    # =====================================================

    def forecast(
        self,
        history: list[dict],
        periods: int = 7,
        window: int = 7,
    ) -> dict:

        if not history:

            return {
                "generated_at": datetime.now(UTC),
                "forecast": [],
                "average_daily": 0,
                "trend": "unknown",
            }

        history = sorted(
            history,
            key=lambda x: x["date"],
        )

        values = [
            int(item["appointments"])
            for item in history
        ]

        last_date = history[-1]["date"]

        forecasts = []

        working = values.copy()

        for i in range(periods):

            recent = working[-window:]

            prediction = round(mean(recent), 2)

            forecast_date = (
                last_date
                + timedelta(days=i + 1)
            )

            forecasts.append(
                {
                    "date": forecast_date,
                    "predicted_appointments": prediction,
                }
            )

            working.append(prediction)

        trend = self._trend(values)

        return {

            "generated_at": datetime.now(UTC),

            "history_points": len(values),

            "average_daily": round(
                mean(values),
                2,
            ),

            "trend": trend,

            "forecast": forecasts,

        }

    # =====================================================
    # Trend Detection
    # =====================================================

    def _trend(
        self,
        values: list[float],
    ) -> str:

        if len(values) < 2:

            return "stable"

        first = mean(
            values[: max(1, len(values) // 2)]
        )

        second = mean(
            values[max(1, len(values) // 2) :]
        )

        if second > first * 1.05:

            return "increasing"

        if second < first * 0.95:

            return "decreasing"

        return "stable"

    # =====================================================
    # Peak Prediction
    # =====================================================

    def predicted_peak(
        self,
        forecast: dict,
    ):

        if not forecast["forecast"]:

            return None

        return max(

            forecast["forecast"],

            key=lambda item: item[
                "predicted_appointments"
            ],

        )

    # =====================================================
    # Lowest Demand
    # =====================================================

    def predicted_low(
        self,
        forecast: dict,
    ):

        if not forecast["forecast"]:

            return None

        return min(

            forecast["forecast"],

            key=lambda item: item[
                "predicted_appointments"
            ],

        )

    # =====================================================
    # Capacity Recommendation
    # =====================================================

    def capacity_recommendation(
        self,
        forecast: dict,
        daily_capacity: int,
    ) -> dict:

        recommendations = []

        for item in forecast["forecast"]:

            predicted = item[
                "predicted_appointments"
            ]

            utilization = round(

                predicted
                / daily_capacity
                * 100,

                2,

            )

            if utilization >= 90:

                action = "Increase staffing"

            elif utilization <= 50:

                action = "Reduce staffing"

            else:

                action = "Normal capacity"

            recommendations.append(

                {

                    "date": item["date"],

                    "predicted": predicted,

                    "capacity": daily_capacity,

                    "utilization": utilization,

                    "recommendation": action,

                }

            )

        return {

            "daily_capacity": daily_capacity,

            "recommendations": recommendations,

        }

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        forecast: dict,
    ) -> dict:

        peak = self.predicted_peak(
            forecast
        )

        low = self.predicted_low(
            forecast
        )

        return {

            "history_points": forecast[
                "history_points"
            ],

            "average_daily": forecast[
                "average_daily"
            ],

            "trend": forecast[
                "trend"
            ],

            "forecast_days": len(
                forecast["forecast"]
            ),

            "peak_prediction": peak,

            "lowest_prediction": low,

        }