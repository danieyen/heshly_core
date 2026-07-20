from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


class DataFilters:
    """
    Analytics Data Filters.

    Provides reusable filtering utilities for analytics,
    dashboards, reports and business intelligence.

    Supports:

        • Date range
        • Today
        • Yesterday
        • This week
        • This month
        • This year
        • Business
        • Customer
        • Employee
        • Status
        • Generic field
        • Numeric range
        • Sorting
        • Limiting
    """

    # =====================================================
    # Generic Helpers
    # =====================================================

    def filter_equals(
        self,
        records: list[dict],
        field: str,
        value: Any,
    ) -> list[dict]:

        return [

            record

            for record in records

            if record.get(field) == value

        ]

    def filter_contains(
        self,
        records: list[dict],
        field: str,
        value: str,
    ) -> list[dict]:

        value = value.lower()

        return [

            record

            for record in records

            if value in str(
                record.get(field, "")
            ).lower()

        ]

    # =====================================================
    # Date Filters
    # =====================================================

    def date_range(
        self,
        records: list[dict],
        field: str,
        start: datetime,
        end: datetime,
    ) -> list[dict]:

        return [

            record

            for record in records

            if start <= record[field] <= end

        ]

    def today(
        self,
        records: list[dict],
        field: str,
    ) -> list[dict]:

        now = datetime.now(UTC)

        start = datetime(

            now.year,

            now.month,

            now.day,

            tzinfo=UTC,

        )

        end = start + timedelta(days=1)

        return self.date_range(

            records,

            field,

            start,

            end,

        )

    def yesterday(
        self,
        records: list[dict],
        field: str,
    ) -> list[dict]:

        today = datetime.now(UTC)

        start = datetime(

            today.year,

            today.month,

            today.day,

            tzinfo=UTC,

        ) - timedelta(days=1)

        end = start + timedelta(days=1)

        return self.date_range(

            records,

            field,

            start,

            end,

        )

    def this_week(
        self,
        records: list[dict],
        field: str,
    ) -> list[dict]:

        now = datetime.now(UTC)

        monday = datetime(

            now.year,

            now.month,

            now.day,

            tzinfo=UTC,

        ) - timedelta(

            days=now.weekday()

        )

        return [

            record

            for record in records

            if record[field] >= monday

        ]

    def this_month(
        self,
        records: list[dict],
        field: str,
    ) -> list[dict]:

        now = datetime.now(UTC)

        return [

            record

            for record in records

            if (

                record[field].year == now.year

                and

                record[field].month == now.month

            )

        ]

    def this_year(
        self,
        records: list[dict],
        field: str,
    ) -> list[dict]:

        year = datetime.now(UTC).year

        return [

            record

            for record in records

            if record[field].year == year

        ]

    # =====================================================
    # Common CRM Filters
    # =====================================================

    def by_business(
        self,
        records: list[dict],
        business_id: str,
    ):

        return self.filter_equals(

            records,

            "business_id",

            business_id,

        )

    def by_customer(
        self,
        records: list[dict],
        customer_id: str,
    ):

        return self.filter_equals(

            records,

            "customer_id",

            customer_id,

        )

    def by_employee(
        self,
        records: list[dict],
        employee_id: str,
    ):

        return self.filter_equals(

            records,

            "employee_id",

            employee_id,

        )

    def by_status(
        self,
        records: list[dict],
        status: str,
    ):

        return self.filter_equals(

            records,

            "status",

            status,

        )

    # =====================================================
    # Numeric Filters
    # =====================================================

    def greater_than(
        self,
        records: list[dict],
        field: str,
        value: float,
    ):

        return [

            record

            for record in records

            if record.get(field, 0) > value

        ]

    def less_than(
        self,
        records: list[dict],
        field: str,
        value: float,
    ):

        return [

            record

            for record in records

            if record.get(field, 0) < value

        ]

    def between(
        self,
        records: list[dict],
        field: str,
        minimum: float,
        maximum: float,
    ):

        return [

            record

            for record in records

            if minimum <= record.get(field, 0) <= maximum

        ]

    # =====================================================
    # Sorting
    # =====================================================

    def sort(
        self,
        records: list[dict],
        field: str,
        reverse: bool = False,
    ):

        return sorted(

            records,

            key=lambda r: r.get(field),

            reverse=reverse,

        )

    def latest(
        self,
        records: list[dict],
        field: str,
        limit: int = 10,
    ):

        return self.sort(

            records,

            field,

            reverse=True,

        )[:limit]

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        records: list[dict],
    ) -> dict:

        return {

            "records": len(records),

        }