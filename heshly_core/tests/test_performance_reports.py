from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class PerformanceResult:

    name: str
    status: str
    duration: float
    throughput: float


class PerformanceReport:

    def __init__(self):

        self.results: list[PerformanceResult] = []

    def add(
        self,
        result: PerformanceResult,
    ):

        self.results.append(result)

    def generate(self) -> str:

        lines = []

        lines.append("HESHLY PERFORMANCE REPORT")
        lines.append("=" * 50)
        lines.append(
            f"Generated: {datetime.now()}"
        )
        lines.append("")

        for result in self.results:

            lines.append(
                f"{result.name}"
            )

            lines.append(
                f"  Status      : {result.status}"
            )

            lines.append(
                f"  Duration    : {result.duration:.3f}s"
            )

            lines.append(
                f"  Throughput  : {result.throughput:.2f}"
            )

            lines.append("")

        return "\n".join(lines)

    def save(
        self,
        filename: str,
    ) -> Path:

        path = Path(filename)

        path.write_text(
            self.generate(),
            encoding="utf-8",
        )

        return path


def test_performance_reports():

    print("\n================================")
    print("Performance Reports")
    print("================================\n")

    report = PerformanceReport()

    report.add(

        PerformanceResult(

            "Load Test",

            "PASSED",

            0.45,

            2200,

        )

    )

    report.add(

        PerformanceResult(

            "Stress Test",

            "PASSED",

            1.82,

            5100,

        )

    )

    report.add(

        PerformanceResult(

            "API Performance",

            "PASSED",

            0.08,

            13000,

        )

    )

    report.add(

        PerformanceResult(

            "Database Performance",

            "PASSED",

            0.11,

            9800,

        )

    )

    report.add(

        PerformanceResult(

            "Queue Performance",

            "PASSED",

            0.32,

            31000,

        )

    )

    file = report.save(
        "performance_report.txt"
    )

    assert file.exists()

    assert file.read_text()

    print(report.generate())

    print("\n🎉 PERFORMANCE REPORT GENERATED\n")