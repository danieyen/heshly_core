from __future__ import annotations

from statistics import mean


class PredictiveAnalytics:
    """
    Predictive Analytics Engine

    Provides lightweight forecasting without external
    machine learning dependencies.

    Uses simple linear trend projection suitable for
    business dashboards and KPI forecasting.
    """

    def __init__(self):

        self.version = "1.0"

    # =====================================================
    # Forecast
    # =====================================================

    def forecast(
        self,
        values: list[float],
        periods: int = 1,
    ) -> dict:

        if not values:

            return {
                "forecast": [],
                "method": "linear",
                "confidence": 0.0,
            }

        slope = self._slope(values)

        current = values[-1]

        predictions = []

        for step in range(1, periods + 1):

            predictions.append(

                round(
                    current + (slope * step),
                    2,
                )

            )

        return {

            "forecast": predictions,

            "method": "linear",

            "trend": self.trend(values),

            "confidence": self.confidence(values),

        }

    # =====================================================
    # Trend
    # =====================================================

    def trend(
        self,
        values: list[float],
    ) -> str:

        slope = self._slope(values)

        if slope > 0:

            return "upward"

        if slope < 0:

            return "downward"

        return "stable"

    # =====================================================
    # Confidence
    # =====================================================

    def confidence(
        self,
        values: list[float],
    ) -> float:

        if len(values) < 3:

            return 0.50

        avg = mean(values)

        if avg == 0:

            return 0.50

        variation = (

            max(values)
            - min(values)

        ) / avg

        confidence = max(

            0.10,

            min(
                1.0,
                1 - (variation / 2),
            ),

        )

        return round(confidence, 2)

    # =====================================================
    # Forecast KPI
    # =====================================================

    def forecast_kpi(
        self,
        metric_name: str,
        values: list[float],
        periods: int = 3,
    ) -> dict:

        result = self.forecast(
            values,
            periods,
        )

        result["metric"] = metric_name

        return result

    # =====================================================
    # Multi Forecast
    # =====================================================

    def forecast_metrics(
        self,
        metrics: dict[str, list[float]],
        periods: int = 3,
    ) -> dict:

        forecasts = {}

        for metric, values in metrics.items():

            forecasts[metric] = (

                self.forecast(
                    values,
                    periods,
                )

            )

        return forecasts

    # =====================================================
    # Growth Projection
    # =====================================================

    def projected_growth(
        self,
        values: list[float],
    ) -> float:

        if len(values) < 2:

            return 0.0

        first = values[0]

        last = values[-1]

        if first == 0:

            return 0.0

        growth = (

            (
                last - first
            )
            / first

        ) * 100

        return round(
            growth,
            2,
        )

    # =====================================================
    # Linear Slope
    # =====================================================

    def _slope(
        self,
        values: list[float],
    ) -> float:

        if len(values) < 2:

            return 0.0

        x = list(range(len(values)))

        x_mean = mean(x)

        y_mean = mean(values)

        numerator = sum(

            (
                xi - x_mean
            )
            * (
                yi - y_mean
            )

            for xi, yi in zip(
                x,
                values,
            )

        )

        denominator = sum(

            (
                xi - x_mean
            ) ** 2

            for xi in x

        )

        if denominator == 0:

            return 0.0

        return numerator / denominator

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "service": "PredictiveAnalytics",

            "version": self.version,

        }