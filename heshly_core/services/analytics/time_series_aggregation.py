from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from statistics import mean


class TimeSeriesAggregation:
    """
    Time Series Aggregation Engine.

    Responsibilities

        • Daily aggregation
        • Weekly aggregation
        • Monthly aggregation
        • Quarterly aggregation
        • Yearly aggregation

        • Sum
        • Count
        • Average
        • Min
        • Max

        • Trend calculations
    """

    def __init__(self):

        self._series: list[dict] = []

    # =====================================================
    # Data Management
    # =====================================================

    def add(
        self,
        timestamp: datetime | date,
        value: float,
    ):

        if isinstance(timestamp, date) and not isinstance(timestamp, datetime):

            timestamp = datetime.combine(
                timestamp,
                datetime.min.time(),
            )

        self._series.append(

            {

                "timestamp": timestamp,

                "value": float(value),

            }

        )

    def extend(
        self,
        records: list[tuple[datetime | date, float]],
    ):

        for timestamp, value in records:

            self.add(timestamp, value)

    def clear(self):

        self._series.clear()

    # =====================================================
    # Aggregation Helpers
    # =====================================================

    def _aggregate(
        self,
        key_function,
        operation: str,
    ) -> dict:

        groups = defaultdict(list)

        for record in self._series:

            key = key_function(

                record["timestamp"]

            )

            groups[key].append(

                record["value"]

            )

        results = {}

        for key, values in sorted(groups.items()):

            if operation == "sum":

                results[key] = sum(values)

            elif operation == "count":

                results[key] = len(values)

            elif operation == "average":

                results[key] = mean(values)

            elif operation == "min":

                results[key] = min(values)

            elif operation == "max":

                results[key] = max(values)

            else:

                raise ValueError(

                    f"Unsupported operation: {operation}"

                )

        return results

    # =====================================================
    # Daily
    # =====================================================

    def daily(
        self,
        operation: str = "sum",
    ):

        return self._aggregate(

            lambda dt: dt.strftime("%Y-%m-%d"),

            operation,

        )

    # =====================================================
    # Weekly
    # =====================================================

    def weekly(
        self,
        operation: str = "sum",
    ):

        return self._aggregate(

            lambda dt: f"{dt.year}-W{dt.isocalendar().week:02d}",

            operation,

        )

    # =====================================================
    # Monthly
    # =====================================================

    def monthly(
        self,
        operation: str = "sum",
    ):

        return self._aggregate(

            lambda dt: dt.strftime("%Y-%m"),

            operation,

        )

    # =====================================================
    # Quarterly
    # =====================================================

    def quarterly(
        self,
        operation: str = "sum",
    ):

        return self._aggregate(

            lambda dt: f"{dt.year}-Q{((dt.month-1)//3)+1}",

            operation,

        )

    # =====================================================
    # Yearly
    # =====================================================

    def yearly(
        self,
        operation: str = "sum",
    ):

        return self._aggregate(

            lambda dt: str(dt.year),

            operation,

        )

    # =====================================================
    # Trend
    # =====================================================

    def trend(self):

        if len(self._series) < 2:

            return 0.0

        ordered = sorted(

            self._series,

            key=lambda r: r["timestamp"],

        )

        first = ordered[0]["value"]

        last = ordered[-1]["value"]

        if first == 0:

            return 0.0

        return round(

            ((last - first) / first) * 100,

            2,

        )

    # =====================================================
    # Statistics
    # =====================================================

    def statistics(self):

        if not self._series:

            return {}

        values = [

            r["value"]

            for r in self._series

        ]

        return {

            "count": len(values),

            "sum": sum(values),

            "average": mean(values),

            "minimum": min(values),

            "maximum": max(values),

            "trend": self.trend(),

        }

    # =====================================================
    # Export
    # =====================================================

    def records(self):

        return list(self._series)