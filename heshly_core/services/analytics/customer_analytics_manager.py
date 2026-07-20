from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.customer_analytics import (
    CustomerAnalyticsPeriod,
)
from heshly_core.services.analytics.customer_lifetime_value import (
    CustomerLifetimeValue,
)
from heshly_core.services.analytics.customer_segmentation import (
    CustomerSegmentation,
)
from heshly_core.services.analytics.retention_analytics import (
    RetentionAnalytics,
)
from heshly_core.services.analytics.churn_prediction import (
    ChurnPrediction,
)
from heshly_core.services.analytics.customer_satisfaction import (
    CustomerSatisfaction,
)


class CustomerAnalyticsManager:
    """
    Customer Analytics Manager

    Coordinates every customer analytics service.

    Modules
    -------
    • Customer Lifetime Value
    • Customer Segmentation
    • Retention Analytics
    • Churn Prediction
    • Customer Satisfaction
    """

    def __init__(self):

        self.clv = CustomerLifetimeValue()

        self.segmentation = CustomerSegmentation()

        self.retention = RetentionAnalytics()

        self.churn = ChurnPrediction()

        self.satisfaction = CustomerSatisfaction()

    # =====================================================
    # Individual Analytics
    # =====================================================

    def lifetime_value(
        self,
        customers: list[dict],
    ):

        return self.clv.analyze(customers)

    def segmentation_report(
        self,
        customers: list[dict],
    ):

        return self.segmentation.analyze(customers)

    def retention_report(
        self,
        customers: list[dict],
    ):

        return self.retention.analyze(customers)

    def churn_report(
        self,
        customers: list[dict],
    ):

        return self.churn.analyze(customers)

    def satisfaction_report(
        self,
        feedback: list[dict],
    ):

        return self.satisfaction.analyze(feedback)

    # =====================================================
    # Complete Customer Analytics
    # =====================================================

    def complete_report(
        self,
        business_id: str,
        customers: list[dict],
        feedback: list[dict],
        period: CustomerAnalyticsPeriod = CustomerAnalyticsPeriod.MONTHLY,
    ) -> dict:

        clv = self.lifetime_value(
            customers
        )

        segmentation = self.segmentation_report(
            customers
        )

        retention = self.retention_report(
            customers
        )

        churn = self.churn_report(
            customers
        )

        satisfaction = self.satisfaction_report(
            feedback
        )

        return {

            "generated_at": datetime.now(UTC),

            "business_id": business_id,

            "period": period.value,

            "customer_lifetime_value": clv,

            "segmentation": segmentation,

            "retention": retention,

            "churn_prediction": churn,

            "customer_satisfaction": satisfaction,

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "status": "healthy",

            "modules": {

                "customer_lifetime_value": True,

                "customer_segmentation": True,

                "retention_analytics": True,

                "churn_prediction": True,

                "customer_satisfaction": True,

            },

        }

    # =====================================================
    # Executive Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        clv = report[
            "customer_lifetime_value"
        ]

        retention = report[
            "retention"
        ]

        churn = report[
            "churn_prediction"
        ]

        satisfaction = report[
            "customer_satisfaction"
        ]

        segmentation = report[
            "segmentation"
        ]

        return {

            "business_id": report[
                "business_id"
            ],

            "period": report[
                "period"
            ],

            "customers": clv[
                "total_customers"
            ],

            "total_revenue": clv[
                "total_revenue"
            ],

            "average_clv": clv[
                "average_clv"
            ],

            "retention_rate": retention[
                "retention_rate"
            ],

            "churn_rate": retention[
                "churn_rate"
            ],

            "high_risk_customers": len(

                self.churn.high_risk(
                    churn
                )

            ),

            "average_rating": satisfaction[
                "average_rating"
            ],

            "csat": satisfaction[
                "csat"
            ],

            "nps": satisfaction[
                "nps"
            ],

            "largest_segment": self.segmentation.largest_segment(
                segmentation
            ),

            "health": self.health(),

        }