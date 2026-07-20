from __future__ import annotations

from statistics import mean

from heshly_core.models.business_intelligence import (
    BIBenchmark,
)


class Benchmarking:
    """
    Business Intelligence Benchmarking

    Compares business performance against targets,
    historical values, or industry benchmarks.
    """

    def __init__(self):

        self.version = "1.0"

    # =====================================================
    # Single Benchmark
    # =====================================================

    def compare(
        self,
        metric: str,
        current: float,
        benchmark: float,
    ) -> BIBenchmark:

        variance = current - benchmark

        if benchmark == 0:

            percent = 0.0

        else:

            percent = (

                variance / benchmark

            ) * 100

        return BIBenchmark(

            metric=metric,

            current_value=current,

            benchmark_value=benchmark,

            variance=round(
                variance,
                2,
            ),

            percentage_variance=round(
                percent,
                2,
            ),

        )

    # =====================================================
    # Multiple Benchmarks
    # =====================================================

    def compare_all(
        self,
        current_metrics: dict[str, float],
        benchmark_metrics: dict[str, float],
    ) -> list[BIBenchmark]:

        results = []

        for metric, current in current_metrics.items():

            benchmark = benchmark_metrics.get(
                metric,
                0.0,
            )

            results.append(

                self.compare(
                    metric,
                    current,
                    benchmark,
                )

            )

        return results

    # =====================================================
    # Score
    # =====================================================

    def performance_score(
        self,
        benchmarks: list[BIBenchmark],
    ) -> float:

        if not benchmarks:

            return 0.0

        scores = []

        for benchmark in benchmarks:

            if benchmark.benchmark_value == 0:

                continue

            score = (

                benchmark.current_value
                / benchmark.benchmark_value

            ) * 100

            scores.append(score)

        if not scores:

            return 0.0

        return round(
            mean(scores),
            2,
        )

    # =====================================================
    # Best Performing Metric
    # =====================================================

    def best_metric(
        self,
        benchmarks: list[BIBenchmark],
    ) -> BIBenchmark | None:

        if not benchmarks:

            return None

        return max(
            benchmarks,
            key=lambda x: x.percentage_variance,
        )

    # =====================================================
    # Worst Performing Metric
    # =====================================================

    def worst_metric(
        self,
        benchmarks: list[BIBenchmark],
    ) -> BIBenchmark | None:

        if not benchmarks:

            return None

        return min(
            benchmarks,
            key=lambda x: x.percentage_variance,
        )

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        current_metrics: dict[str, float],
        benchmark_metrics: dict[str, float],
    ) -> dict:

        benchmarks = self.compare_all(
            current_metrics,
            benchmark_metrics,
        )

        best = self.best_metric(
            benchmarks
        )

        worst = self.worst_metric(
            benchmarks
        )

        return {

            "benchmarks": benchmarks,

            "performance_score":
                self.performance_score(
                    benchmarks
                ),

            "best_metric":
                best.metric if best else None,

            "worst_metric":
                worst.metric if worst else None,

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "service": "Benchmarking",

            "version": self.version,

        }