from __future__ import annotations

from statistics import mean


class TrendAnalysis:
    """
    Business Intelligence Trend Analysis

    Provides trend detection and growth calculations
    for time-series business metrics.
    """

    def __init__(self):

        self.version = "1.0"

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        values: list[float],
    ) -> dict:

        if not values:

            return {
                "trend": "unknown",
                "growth": 0.0,
                "average": 0.0,
                "minimum": 0.0,
                "maximum": 0.0,
                "points": 0,
            }

        growth = self.growth_rate(values)

        return {

            "trend": self.classify(values),

            "growth": round(growth, 2),

            "average": round(mean(values), 2),

            "minimum": min(values),

            "maximum": max(values),

            "points": len(values),

        }

    # =====================================================
    # Growth Rate
    # =====================================================

    def growth_rate(
        self,
        values: list[float],
    ) -> float:

        if len(values) < 2:

            return 0.0

        start = values[0]

        end = values[-1]

        if start == 0:

            return 0.0

        return ((end - start) / start) * 100

    # =====================================================
    # Trend Classification
    # =====================================================

    def classify(
        self,
        values: list[float],
    ) -> str:

        if len(values) < 2:

            return "stable"

        increasing = all(

            values[i] >= values[i - 1]

            for i in range(1, len(values))

        )

        decreasing = all(

            values[i] <= values[i - 1]

            for i in range(1, len(values))

        )

        if increasing:

            return "increasing"

        if decreasing:

            return "decreasing"

        return "fluctuating"

    # =====================================================
    # Moving Average
    # =====================================================

    def moving_average(
        self,
        values: list[float],
        window: int = 3,
    ) -> list[float]:

        if window <= 0:

            raise ValueError(
                "window must be positive"
            )

        if len(values) < window:

            return []

        averages = []

        for i in range(

            len(values) - window + 1

        ):

            averages.append(

                round(

                    mean(

                        values[
                            i : i + window
                        ]
                    ),

                    2,

                )

            )

        return averages

    # =====================================================
    # Period-over-Period Change
    # =====================================================

    def changes(
        self,
        values: list[float],
    ) -> list[float]:

        if len(values) < 2:

            return []

        results = []

        for previous, current in zip(

            values,

            values[1:],

        ):

            if previous == 0:

                results.append(0.0)

            else:

                results.append(

                    round(

                        (

                            (
                                current
                                - previous
                            )
                            / previous
                        )
                        * 100,

                        2,

                    )

                )

        return results

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        values: list[float],
    ) -> dict:

        report = self.analyze(values)

        report["moving_average"] = (

            self.moving_average(values)

        )

        report["changes"] = (

            self.changes(values)

        )

        return report

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "service": "TrendAnalysis",

            "version": self.version,

        }