from __future__ import annotations

from datetime import UTC, datetime


class ChurnPrediction:
    """
    Customer Churn Prediction

    A simple rule-based churn scoring engine.

    Expected customer format

    {
        "customer_id": "...",
        "customer_name": "...",
        "appointments": 8,
        "completed_appointments": 6,
        "cancelled_appointments": 1,
        "no_shows": 1,
        "total_spent": 35000,
        "last_visit": datetime(...)
    }
    """

    def __init__(
        self,
        low_risk_threshold: int = 30,
        medium_risk_threshold: int = 60,
        high_risk_threshold: int = 80,
    ):

        self.low_threshold = low_risk_threshold
        self.medium_threshold = medium_risk_threshold
        self.high_threshold = high_risk_threshold

    # =====================================================
    # Predict One Customer
    # =====================================================

    def predict_customer(
        self,
        customer: dict,
    ) -> dict:

        score = 0

        reasons = []

        today = datetime.now(UTC)

        visits = int(customer.get("appointments", 0))

        completed = int(
            customer.get(
                "completed_appointments",
                0,
            )
        )

        cancelled = int(
            customer.get(
                "cancelled_appointments",
                0,
            )
        )

        no_shows = int(
            customer.get(
                "no_shows",
                0,
            )
        )

        spent = float(
            customer.get(
                "total_spent",
                0,
            )
        )

        last_visit = customer.get(
            "last_visit"
        )

        # ---------------------------------------------
        # Visit Recency
        # ---------------------------------------------

        if isinstance(last_visit, datetime):

            days = (
                today - last_visit
            ).days

            if days > 180:

                score += 40

                reasons.append(
                    "No visit in over 180 days"
                )

            elif days > 90:

                score += 25

                reasons.append(
                    "No visit in over 90 days"
                )

            elif days > 60:

                score += 15

                reasons.append(
                    "No visit in over 60 days"
                )

        # ---------------------------------------------
        # Visit Frequency
        # ---------------------------------------------

        if visits <= 1:

            score += 20

            reasons.append(
                "Very few appointments"
            )

        elif visits <= 3:

            score += 10

            reasons.append(
                "Low appointment frequency"
            )

        # ---------------------------------------------
        # Cancellation
        # ---------------------------------------------

        if cancelled >= 3:

            score += 20

            reasons.append(
                "Frequent cancellations"
            )

        elif cancelled >= 1:

            score += 10

            reasons.append(
                "Recent cancellation"
            )

        # ---------------------------------------------
        # No Shows
        # ---------------------------------------------

        if no_shows >= 2:

            score += 15

            reasons.append(
                "Repeated no-shows"
            )

        elif no_shows == 1:

            score += 8

            reasons.append(
                "Recent no-show"
            )

        # ---------------------------------------------
        # Spending
        # ---------------------------------------------

        if spent < 5000:

            score += 10

            reasons.append(
                "Low customer value"
            )

        # ---------------------------------------------
        # Loyalty Bonus
        # ---------------------------------------------

        if completed >= 10:

            score -= 15

        elif completed >= 5:

            score -= 8

        score = max(0, min(score, 100))

        if score >= self.high_threshold:

            risk = "High"

        elif score >= self.medium_threshold:

            risk = "Medium"

        elif score >= self.low_threshold:

            risk = "Low"

        else:

            risk = "Very Low"

        return {

            "customer_id": customer.get(
                "customer_id"
            ),

            "customer_name": customer.get(
                "customer_name",
                "Unknown",
            ),

            "risk_score": score,

            "risk_level": risk,

            "reasons": reasons,

        }

    # =====================================================
    # Analyze Customers
    # =====================================================

    def analyze(
        self,
        customers: list[dict],
    ) -> dict:

        predictions = [

            self.predict_customer(customer)

            for customer in customers

        ]

        breakdown = {

            "Very Low": 0,

            "Low": 0,

            "Medium": 0,

            "High": 0,

        }

        for prediction in predictions:

            breakdown[
                prediction["risk_level"]
            ] += 1

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "customers": predictions,

            "total_customers": len(
                predictions
            ),

            "risk_breakdown": breakdown,

        }

    # =====================================================
    # Filters
    # =====================================================

    def high_risk(
        self,
        report: dict,
    ):

        return [

            customer

            for customer in report["customers"]

            if customer["risk_level"] == "High"

        ]

    def medium_risk(
        self,
        report: dict,
    ):

        return [

            customer

            for customer in report["customers"]

            if customer["risk_level"] == "Medium"

        ]

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ):

        return {

            "customers": report[
                "total_customers"
            ],

            "risk_breakdown": report[
                "risk_breakdown"
            ],

            "high_risk_customers": len(
                self.high_risk(report)
            ),

            "medium_risk_customers": len(
                self.medium_risk(report)
            ),

        }