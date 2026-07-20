from __future__ import annotations

from math import sqrt
from statistics import mean


class AnomalyDetection:
    """
    Business Intelligence Anomaly Detection

    Detects unusual values in business metrics using
    Z-score analysis.
    """

    def __init__(self):

        self.version = "1.0"

    # =====================================================
    # Detect Anomalies
    # =====================================================

    def detect(
        self,
        values: list[float],
        threshold: float = 2.0,
    ) -> dict:

        if len(values) < 2:

            return {

                "anomalies": [],

                "count": 0,

                "threshold": threshold,

                "mean": 0.0,

                "std_dev": 0.0,

            }

        avg = mean(values)

        std = self.standard_deviation(values)

        if std == 0:

            return {

                "anomalies": [],

                "count": 0,

                "threshold": threshold,

                "mean": avg,

                "std_dev": std,

            }

        anomalies = []

        for index, value in enumerate(values):

            z = abs((value - avg) / std)

            if z >= threshold:

                anomalies.append(

                    {

                        "index": index,

                        "value": value,

                        "z_score": round(z, 2),

                    }

                )

        return {

            "anomalies": anomalies,

            "count": len(anomalies),

            "threshold": threshold,

            "mean": round(avg, 2),

            "std_dev": round(std, 2),

        }

    # =====================================================
    # Z-Score
    # =====================================================

    def z_scores(
        self,
        values: list[float],
    ) -> list[float]:

        if len(values) < 2:

            return []

        avg = mean(values)

        std = self.standard_deviation(values)

        if std == 0:

            return [0.0] * len(values)

        return [

            round(

                (value - avg) / std,

                3,

            )

            for value in values

        ]

    # =====================================================
    # Standard Deviation
    # =====================================================

    def standard_deviation(
        self,
        values: list[float],
    ) -> float:

        if len(values) < 2:

            return 0.0

        avg = mean(values)

        variance = sum(

            (value - avg) ** 2

            for value in values

        ) / len(values)

        return sqrt(variance)

    # =====================================================
    # Health Score
    # =====================================================

    def health_score(
        self,
        values: list[float],
    ) -> float:

        report = self.detect(values)

        if not values:

            return 100.0

        score = (

            1
            - (
                report["count"]
                / len(values)
            )

        ) * 100

        return round(

            max(0.0, score),

            2,

        )

    # =====================================================
    # Business Health
    # =====================================================

    def business_health(
        self,
        metrics: dict[str, list[float]],
    ) -> dict:

        results = {}

        scores = []

        for name, values in metrics.items():

            report = self.detect(values)

            score = self.health_score(values)

            scores.append(score)

            results[name] = {

                "health_score": score,

                "anomalies": report["count"],

            }

        overall = (

            round(

                mean(scores),

                2,

            )

            if scores

            else 100.0

        )

        return {

            "overall_health": overall,

            "metrics": results,

        }

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        values: list[float],
    ) -> dict:

        report = self.detect(values)

        report["health_score"] = self.health_score(values)

        report["z_scores"] = self.z_scores(values)

        return report

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "service": "AnomalyDetection",

            "version": self.version,

        }