from __future__ import annotations

from datetime import UTC, datetime
from statistics import mean
from typing import Any

from heshly_core.models.analytics import (
    Metric,
    MetricType,
)


class MetricsEngine:
    """
    Core analytics metrics engine.

    Responsible for:

        • Count metrics
        • Sum metrics
        • Average metrics
        • Percentage metrics
        • Ratio metrics
        • Currency metrics
        • Duration metrics
        • Score metrics
        • Metric registry
    """

    def __init__(self):

        self._metrics: dict[str, Metric] = {}

    # =====================================================
    # Metric Management
    # =====================================================

    def register(
        self,
        metric: Metric,
    ) -> Metric:

        metric.updated_at = datetime.now(UTC)

        self._metrics[
            metric.metric_id
        ] = metric

        return metric

    def get(
        self,
        metric_id: str,
    ) -> Metric | None:

        return self._metrics.get(
            metric_id
        )

    def all(self) -> list[Metric]:

        return list(
            self._metrics.values()
        )

    def delete(
        self,
        metric_id: str,
    ) -> bool:

        return (
            self._metrics.pop(
                metric_id,
                None,
            )
            is not None
        )

    def clear(self):

        self._metrics.clear()

    # =====================================================
    # Metric Builders
    # =====================================================

    def count(
        self,
        metric_id: str,
        name: str,
        values: list[Any],
        description: str = "",
    ) -> Metric:

        metric = Metric(

            metric_id=metric_id,

            name=name,

            metric_type=MetricType.COUNT,

            value=float(len(values)),

            description=description,

        )

        return self.register(
            metric
        )

    def total(
        self,
        metric_id: str,
        name: str,
        values: list[float],
        description: str = "",
    ) -> Metric:

        metric = Metric(

            metric_id=metric_id,

            name=name,

            metric_type=MetricType.SUM,

            value=float(sum(values)),

            description=description,

        )

        return self.register(
            metric
        )

    def average(
        self,
        metric_id: str,
        name: str,
        values: list[float],
        description: str = "",
    ) -> Metric:

        value = (
            mean(values)
            if values
            else 0.0
        )

        metric = Metric(

            metric_id=metric_id,

            name=name,

            metric_type=MetricType.AVERAGE,

            value=float(value),

            description=description,

        )

        return self.register(
            metric
        )

    def percentage(
        self,
        metric_id: str,
        name: str,
        numerator: float,
        denominator: float,
        description: str = "",
    ) -> Metric:

        value = 0.0

        if denominator > 0:

            value = (
                numerator
                / denominator
            ) * 100

        metric = Metric(

            metric_id=metric_id,

            name=name,

            metric_type=MetricType.PERCENTAGE,

            value=round(value, 2),

            unit="%",

            description=description,

        )

        return self.register(
            metric
        )

    def ratio(
        self,
        metric_id: str,
        name: str,
        left: float,
        right: float,
        description: str = "",
    ) -> Metric:

        value = 0.0

        if right > 0:

            value = left / right

        metric = Metric(

            metric_id=metric_id,

            name=name,

            metric_type=MetricType.RATIO,

            value=round(value, 4),

            description=description,

        )

        return self.register(
            metric
        )

    def currency(
        self,
        metric_id: str,
        name: str,
        amount: float,
        currency: str = "KES",
        description: str = "",
    ) -> Metric:

        metric = Metric(

            metric_id=metric_id,

            name=name,

            metric_type=MetricType.CURRENCY,

            value=float(amount),

            unit=currency,

            description=description,

        )

        return self.register(
            metric
        )

    def duration(
        self,
        metric_id: str,
        name: str,
        minutes: float,
        description: str = "",
    ) -> Metric:

        metric = Metric(

            metric_id=metric_id,

            name=name,

            metric_type=MetricType.DURATION,

            value=float(minutes),

            unit="minutes",

            description=description,

        )

        return self.register(
            metric
        )

    def score(
        self,
        metric_id: str,
        name: str,
        value: float,
        max_score: float = 100.0,
        description: str = "",
    ) -> Metric:

        metric = Metric(

            metric_id=metric_id,

            name=name,

            metric_type=MetricType.SCORE,

            value=float(value),

            unit=f"/{max_score}",

            description=description,

        )

        return self.register(
            metric
        )

    # =====================================================
    # Helpers
    # =====================================================

    def exists(
        self,
        metric_id: str,
    ) -> bool:

        return (
            metric_id
            in self._metrics
        )

    def summary(self) -> dict:

        totals = {}

        for metric in self._metrics.values():

            metric_type = (
                metric.metric_type.value
            )

            totals[metric_type] = (
                totals.get(
                    metric_type,
                    0,
                )
                + 1
            )

        return {

            "total_metrics": len(
                self._metrics
            ),

            "breakdown": totals,

        }