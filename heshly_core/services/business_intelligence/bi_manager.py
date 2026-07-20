from __future__ import annotations

from heshly_core.services.business_intelligence.trend_analysis import (
    TrendAnalysis,
)
from heshly_core.services.business_intelligence.predictive_analytics import (
    PredictiveAnalytics,
)
from heshly_core.services.business_intelligence.anomaly_detection import (
    AnomalyDetection,
)
from heshly_core.services.business_intelligence.benchmarking import (
    Benchmarking,
)
from heshly_core.services.business_intelligence.recommendation_engine import (
    RecommendationEngine,
)


class BIManager:
    """
    Business Intelligence Manager

    Coordinates all Business Intelligence services.

    Components
    ----------
    • Trend Analysis
    • Predictive Analytics
    • Anomaly Detection
    • Benchmarking
    • Recommendation Engine
    """

    def __init__(self):

        self.trends = TrendAnalysis()

        self.predictions = PredictiveAnalytics()

        self.anomalies = AnomalyDetection()

        self.benchmarking = Benchmarking()

        self.recommendations = RecommendationEngine()

    # =====================================================
    # Complete Analysis
    # =====================================================

    def analyze(
        self,
        metric_name: str,
        values: list[float],
        benchmark: float | None = None,
    ) -> dict:

        trend = self.trends.summary(values)

        prediction = self.predictions.forecast_kpi(
            metric_name,
            values,
        )

        anomaly = self.anomalies.summary(values)

        benchmark_summary = {}

        if benchmark is not None and values:

            benchmark_summary = self.benchmarking.summary(

                current_metrics={
                    metric_name: values[-1],
                },

                benchmark_metrics={
                    metric_name: benchmark,
                },

            )

        recommendations = self.recommendations.generate(

            trends=trend,

            anomalies=anomaly,

            benchmarks=benchmark_summary
            if benchmark_summary
            else None,

        )

        recommendation_summary = (
            self.recommendations.summary(
                recommendations
            )
        )

        return {

            "metric": metric_name,

            "trend": trend,

            "prediction": prediction,

            "anomalies": anomaly,

            "benchmark": benchmark_summary,

            "recommendations": recommendations,

            "recommendation_summary":
                recommendation_summary,

        }

    # =====================================================
    # Multi-Metric Analysis
    # =====================================================

    def analyze_metrics(
        self,
        metrics: dict[str, list[float]],
    ) -> dict:

        results = {}

        for name, values in metrics.items():

            results[name] = self.analyze(
                metric_name=name,
                values=values,
            )

        return results

    # =====================================================
    # KPI Forecasts
    # =====================================================

    def forecast(
        self,
        metrics: dict[str, list[float]],
        periods: int = 3,
    ) -> dict:

        return self.predictions.forecast_metrics(
            metrics,
            periods,
        )

    # =====================================================
    # Business Health
    # =====================================================

    def business_health(
        self,
        metrics: dict[str, list[float]],
    ) -> dict:

        return self.anomalies.business_health(
            metrics
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "services": {

                "trend_analysis":
                    self.trends.health(),

                "predictive_analytics":
                    self.predictions.health(),

                "anomaly_detection":
                    self.anomalies.health(),

                "benchmarking":
                    self.benchmarking.health(),

                "recommendation_engine":
                    self.recommendations.health(),

            },

        }