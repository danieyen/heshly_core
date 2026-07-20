from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from heshly_core.models.customer_analytics import (
    CustomerSegment,
)


class CustomerSegmentation:
    """
    Customer Segmentation

    Default segmentation rules

        VIP
            Lifetime spend >= vip_spend

        Lost
            No visit for >= lost_days

        At Risk
            No visit for >= at_risk_days

        Returning
            Visits >= returning_visits

        Active
            Visits >= active_visits

        New
            Everyone else

    Expected customer dictionary

    {
        "customer_id": "...",
        "customer_name": "...",
        "visits": 6,
        "appointments": 6,
        "completed_appointments": 5,
        "total_spent": 55000,
        "last_visit": datetime(...),
        "first_visit": datetime(...)
    }
    """

    def __init__(
        self,
        vip_spend: float = 50000,
        active_visits: int = 2,
        returning_visits: int = 5,
        at_risk_days: int = 60,
        lost_days: int = 180,
    ):

        self.vip_spend = vip_spend
        self.active_visits = active_visits
        self.returning_visits = returning_visits
        self.at_risk_days = at_risk_days
        self.lost_days = lost_days

    # =====================================================
    # Segment One Customer
    # =====================================================

    def segment_customer(
        self,
        customer: dict,
    ) -> CustomerSegment:

        visits = int(customer.get("visits", 0))
        spent = float(customer.get("total_spent", 0))

        last_visit = customer.get("last_visit")

        days_since_visit = 0

        if isinstance(last_visit, datetime):

            days_since_visit = (
                datetime.now(UTC) - last_visit
            ).days

        if spent >= self.vip_spend:
            return CustomerSegment.VIP

        if days_since_visit >= self.lost_days:
            return CustomerSegment.LOST

        if days_since_visit >= self.at_risk_days:
            return CustomerSegment.AT_RISK

        if visits >= self.returning_visits:
            return CustomerSegment.RETURNING

        if visits >= self.active_visits:
            return CustomerSegment.ACTIVE

        return CustomerSegment.NEW

    # =====================================================
    # Segment Portfolio
    # =====================================================

    def analyze(
        self,
        customers: list[dict],
    ) -> dict:

        segmented = []

        counter = Counter()

        revenue = Counter()

        for customer in customers:

            segment = self.segment_customer(
                customer
            )

            spent = float(
                customer.get(
                    "total_spent",
                    0,
                )
            )

            counter[segment.value] += 1
            revenue[segment.value] += spent

            segmented.append(
                {
                    **customer,
                    "segment": segment.value,
                }
            )

        summaries = []

        for segment_name, count in counter.items():

            total_revenue = revenue[
                segment_name
            ]

            summaries.append(
                {
                    "segment": segment_name,
                    "customers": count,
                    "revenue": round(
                        total_revenue,
                        2,
                    ),
                    "average_value": round(
                        total_revenue / count,
                        2,
                    ),
                }
            )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "customers": segmented,

            "segment_breakdown": dict(counter),

            "segment_summary": summaries,

            "total_customers": len(
                customers
            ),

        }

    # =====================================================
    # Filters
    # =====================================================

    def customers_in_segment(
        self,
        report: dict,
        segment: CustomerSegment,
    ):

        return [

            customer

            for customer in report["customers"]

            if customer["segment"]
            == segment.value

        ]

    # =====================================================
    # Rankings
    # =====================================================

    def largest_segment(
        self,
        report: dict,
    ):

        if not report["segment_breakdown"]:
            return None

        return max(

            report[
                "segment_breakdown"
            ].items(),

            key=lambda item: item[1],

        )

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

            "segments": len(
                report[
                    "segment_breakdown"
                ]
            ),

            "largest_segment": self.largest_segment(
                report
            ),

            "vip_customers": len(
                self.customers_in_segment(
                    report,
                    CustomerSegment.VIP,
                )
            ),

            "at_risk_customers": len(
                self.customers_in_segment(
                    report,
                    CustomerSegment.AT_RISK,
                )
            ),

            "lost_customers": len(
                self.customers_in_segment(
                    report,
                    CustomerSegment.LOST,
                )
            ),

        }