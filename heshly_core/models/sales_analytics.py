from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# ==========================================================
# Analytics Period
# ==========================================================

class SalesAnalyticsPeriod(str, Enum):

    DAILY = "daily"

    WEEKLY = "weekly"

    MONTHLY = "monthly"

    QUARTERLY = "quarterly"

    YEARLY = "yearly"

    CUSTOM = "custom"


# ==========================================================
# Sales Metrics
# ==========================================================

@dataclass(slots=True)
class SalesMetrics:

    total_quotes: int = 0

    accepted_quotes: int = 0

    rejected_quotes: int = 0

    expired_quotes: int = 0

    total_sales: int = 0

    total_revenue: float = 0.0

    average_sale_value: float = 0.0

    highest_sale: float = 0.0

    lowest_sale: float = 0.0

    conversion_rate: float = 0.0


# ==========================================================
# Sales Record
# ==========================================================

@dataclass(slots=True)
class SalesRecord:

    sale_id: str

    customer_id: str

    customer_name: str

    quote_id: str | None = None

    employee_name: str = ""

    service_name: str = ""

    sale_date: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    amount: float = 0.0

    quantity: int = 1

    discount: float = 0.0

    tax: float = 0.0

    total: float = 0.0

    payment_method: str = "Cash"

    status: str = "completed"

    metadata: dict = field(
        default_factory=dict
    )


# ==========================================================
# Revenue Breakdown
# ==========================================================

@dataclass(slots=True)
class RevenueBreakdown:

    category: str

    revenue: float = 0.0

    sales: int = 0

    average_sale: float = 0.0


# ==========================================================
# Sales Analytics Report
# ==========================================================

@dataclass(slots=True)
class SalesAnalyticsReport:

    report_id: str

    business_id: str

    period: SalesAnalyticsPeriod

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    metrics: SalesMetrics = field(
        default_factory=SalesMetrics
    )

    sales: list[SalesRecord] = field(
        default_factory=list
    )

    revenue_breakdown: list[
        RevenueBreakdown
    ] = field(
        default_factory=list
    )

    total_revenue: float = 0.0

    metadata: dict = field(
        default_factory=dict
    )

    # ======================================================
    # Helpers
    # ======================================================

    def add_sale(
        self,
        sale: SalesRecord,
    ):

        self.sales.append(sale)

    def add_breakdown(
        self,
        breakdown: RevenueBreakdown,
    ):

        self.revenue_breakdown.append(
            breakdown
        )

    @property
    def total_sales_records(self) -> int:

        return len(self.sales)

    @property
    def total_breakdowns(self) -> int:

        return len(self.revenue_breakdown)