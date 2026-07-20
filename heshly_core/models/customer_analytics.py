from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# ==========================================================
# Analytics Period
# ==========================================================

class CustomerAnalyticsPeriod(str, Enum):

    DAILY = "daily"

    WEEKLY = "weekly"

    MONTHLY = "monthly"

    QUARTERLY = "quarterly"

    YEARLY = "yearly"

    CUSTOM = "custom"


# ==========================================================
# Customer Segment
# ==========================================================

class CustomerSegment(str, Enum):

    NEW = "new"

    ACTIVE = "active"

    RETURNING = "returning"

    VIP = "vip"

    AT_RISK = "at_risk"

    LOST = "lost"


# ==========================================================
# Customer Metrics
# ==========================================================

@dataclass(slots=True)
class CustomerMetrics:

    total_customers: int = 0

    new_customers: int = 0

    active_customers: int = 0

    returning_customers: int = 0

    vip_customers: int = 0

    at_risk_customers: int = 0

    lost_customers: int = 0

    average_lifetime_value: float = 0.0

    average_visits: float = 0.0

    retention_rate: float = 0.0

    churn_rate: float = 0.0


# ==========================================================
# Customer Record
# ==========================================================

@dataclass(slots=True)
class CustomerAnalyticsRecord:

    customer_id: str

    customer_name: str

    segment: CustomerSegment = CustomerSegment.NEW

    visits: int = 0

    appointments: int = 0

    completed_appointments: int = 0

    cancelled_appointments: int = 0

    no_shows: int = 0

    total_spent: float = 0.0

    average_order_value: float = 0.0

    lifetime_value: float = 0.0

    last_visit: datetime | None = None

    first_visit: datetime | None = None

    acquisition_source: str = "Unknown"

    metadata: dict = field(default_factory=dict)


# ==========================================================
# Customer Segment Summary
# ==========================================================

@dataclass(slots=True)
class CustomerSegmentSummary:

    segment: CustomerSegment

    customers: int = 0

    revenue: float = 0.0

    average_value: float = 0.0


# ==========================================================
# Customer Analytics Report
# ==========================================================

@dataclass(slots=True)
class CustomerAnalyticsReport:

    report_id: str

    business_id: str

    period: CustomerAnalyticsPeriod

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    metrics: CustomerMetrics = field(
        default_factory=CustomerMetrics
    )

    customers: list[
        CustomerAnalyticsRecord
    ] = field(
        default_factory=list
    )

    segments: list[
        CustomerSegmentSummary
    ] = field(
        default_factory=list
    )

    total_revenue: float = 0.0

    average_customer_value: float = 0.0

    metadata: dict = field(
        default_factory=dict
    )

    # ======================================================
    # Helpers
    # ======================================================

    def add_customer(
        self,
        customer: CustomerAnalyticsRecord,
    ):

        self.customers.append(customer)

    def add_segment(
        self,
        segment: CustomerSegmentSummary,
    ):

        self.segments.append(segment)

    @property
    def total_customer_records(self) -> int:

        return len(self.customers)

    @property
    def total_segments(self) -> int:

        return len(self.segments)