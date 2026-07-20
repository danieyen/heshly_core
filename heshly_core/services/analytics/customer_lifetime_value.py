from __future__ import annotations

from datetime import UTC, datetime
from statistics import mean


class CustomerLifetimeValue:
    """
    Customer Lifetime Value (CLV)

    Calculates lifetime value metrics for customers.

    Expected customer format:

    {
        "customer_id": "...",
        "customer_name": "...",
        "appointments": 12,
        "completed_appointments": 10,
        "total_spent": 45000,
        "first_visit": datetime(...),
        "last_visit": datetime(...)
    }
    """

    # =====================================================
    # Individual CLV
    # =====================================================

    def calculate_customer(
        self,
        customer: dict,
    ) -> dict:

        completed = int(
            customer.get(
                "completed_appointments",
                customer.get(
                    "appointments",
                    0,
                ),
            )
        )

        total_spent = float(
            customer.get(
                "total_spent",
                0.0,
            )
        )

        average_order_value = (
            round(
                total_spent / completed,
                2,
            )
            if completed
            else 0.0
        )

        first_visit = customer.get(
            "first_visit"
        )

        last_visit = customer.get(
            "last_visit"
        )

        lifespan_days = 0

        if (
            isinstance(first_visit, datetime)
            and isinstance(last_visit, datetime)
        ):

            lifespan_days = max(
                (
                    last_visit
                    - first_visit
                ).days,
                0,
            )

        return {

            "customer_id": customer.get(
                "customer_id"
            ),

            "customer_name": customer.get(
                "customer_name",
                "Unknown",
            ),

            "completed_appointments": completed,

            "total_spent": total_spent,

            "average_order_value": average_order_value,

            "lifetime_value": round(
                total_spent,
                2,
            ),

            "lifespan_days": lifespan_days,

        }

    # =====================================================
    # Portfolio CLV
    # =====================================================

    def analyze(
        self,
        customers: list[dict],
    ) -> dict:

        records = [

            self.calculate_customer(
                customer
            )

            for customer in customers

        ]

        total_customers = len(records)

        total_revenue = sum(

            record[
                "lifetime_value"
            ]

            for record in records

        )

        average_clv = (
            round(
                total_revenue
                / total_customers,
                2,
            )
            if total_customers
            else 0.0
        )

        average_order_value = (
            round(

                mean(

                    record[
                        "average_order_value"
                    ]

                    for record in records

                ),

                2,

            )
            if records
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "customers": records,

            "total_customers": total_customers,

            "total_revenue": round(
                total_revenue,
                2,
            ),

            "average_clv": average_clv,

            "average_order_value": average_order_value,

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_customers(
        self,
        report: dict,
        limit: int = 10,
    ):

        return sorted(

            report["customers"],

            key=lambda record: record[
                "lifetime_value"
            ],

            reverse=True,

        )[:limit]

    def lowest_customers(
        self,
        report: dict,
        limit: int = 10,
    ):

        return sorted(

            report["customers"],

            key=lambda record: record[
                "lifetime_value"
            ],

        )[:limit]

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        return {

            "customers": report[
                "total_customers"
            ],

            "total_revenue": report[
                "total_revenue"
            ],

            "average_clv": report[
                "average_clv"
            ],

            "average_order_value": report[
                "average_order_value"
            ],

            "highest_value_customer": self.top_customers(
                report,
                1,
            ),

        }