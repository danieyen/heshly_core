from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime


class RetentionAnalytics:
    """
    Customer Retention Analytics

    Measures customer retention and churn.

    Expected customer format

    {
        "customer_id": "...",
        "customer_name": "...",
        "first_visit": datetime(...),
        "last_visit": datetime(...),
        "appointments": 5,
        "completed_appointments": 4
    }
    """

    def __init__(
        self,
        active_days: int = 90,
        lost_days: int = 180,
    ):

        self.active_days = active_days
        self.lost_days = lost_days

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        customers: list[dict],
    ) -> dict:

        today = datetime.now(UTC)

        active = 0
        retained = 0
        lost = 0
        new = 0

        age_distribution = Counter()
        visit_distribution = Counter()

        analyzed = []

        for customer in customers:

            first_visit = customer.get("first_visit")
            last_visit = customer.get("last_visit")

            visits = int(
                customer.get("appointments", 0)
            )

            days_since_last = None
            customer_age = None

            if isinstance(last_visit, datetime):
                days_since_last = (
                    today - last_visit
                ).days

            if isinstance(first_visit, datetime):
                customer_age = (
                    today - first_visit
                ).days

            if customer_age is not None:

                if customer_age <= 30:
                    age_distribution["0-30"] += 1
                elif customer_age <= 90:
                    age_distribution["31-90"] += 1
                elif customer_age <= 180:
                    age_distribution["91-180"] += 1
                elif customer_age <= 365:
                    age_distribution["181-365"] += 1
                else:
                    age_distribution["365+"] += 1

            if visits == 1:
                visit_distribution["1"] += 1
            elif visits <= 3:
                visit_distribution["2-3"] += 1
            elif visits <= 5:
                visit_distribution["4-5"] += 1
            elif visits <= 10:
                visit_distribution["6-10"] += 1
            else:
                visit_distribution["10+"] += 1

            if visits == 1:
                new += 1

            if days_since_last is None:

                status = "unknown"

            elif days_since_last <= self.active_days:

                status = "active"
                active += 1

                if visits > 1:
                    retained += 1

            elif days_since_last >= self.lost_days:

                status = "lost"
                lost += 1

            else:

                status = "inactive"

            analyzed.append(
                {
                    **customer,
                    "status": status,
                    "days_since_last": days_since_last,
                    "customer_age_days": customer_age,
                }
            )

        total = len(customers)

        retention_rate = (
            round(retained / total * 100, 2)
            if total
            else 0.0
        )

        churn_rate = (
            round(lost / total * 100, 2)
            if total
            else 0.0
        )

        return {

            "generated_at": datetime.now(UTC),

            "customers": analyzed,

            "total_customers": total,

            "active_customers": active,

            "retained_customers": retained,

            "lost_customers": lost,

            "new_customers": new,

            "retention_rate": retention_rate,

            "churn_rate": churn_rate,

            "age_distribution": dict(
                age_distribution
            ),

            "visit_distribution": dict(
                visit_distribution
            ),

        }

    # =====================================================
    # Filters
    # =====================================================

    def active_customers(
        self,
        report: dict,
    ):

        return [
            customer
            for customer in report["customers"]
            if customer["status"] == "active"
        ]

    def lost_customers(
        self,
        report: dict,
    ):

        return [
            customer
            for customer in report["customers"]
            if customer["status"] == "lost"
        ]

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        return {

            "customers": report["total_customers"],

            "active": report["active_customers"],

            "retained": report[
                "retained_customers"
            ],

            "lost": report["lost_customers"],

            "new": report["new_customers"],

            "retention_rate": report[
                "retention_rate"
            ],

            "churn_rate": report[
                "churn_rate"
            ],

            "active_customer_records": len(
                self.active_customers(report)
            ),

            "lost_customer_records": len(
                self.lost_customers(report)
            ),

        }