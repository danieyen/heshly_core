from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# ==========================================================
# Analytics Period
# ==========================================================

class AnalyticsPeriod(str, Enum):

    DAILY = "daily"

    WEEKLY = "weekly"

    MONTHLY = "monthly"

    QUARTERLY = "quarterly"

    YEARLY = "yearly"

    CUSTOM = "custom"


# ==========================================================
# Appointment Status Metrics
# ==========================================================

@dataclass(slots=True)
class AppointmentStatusMetrics:

    scheduled: int = 0

    confirmed: int = 0

    completed: int = 0

    cancelled: int = 0

    no_show: int = 0

    rescheduled: int = 0

    pending: int = 0

    @property
    def total(self) -> int:

        return (

            self.scheduled
            + self.confirmed
            + self.completed
            + self.cancelled
            + self.no_show
            + self.rescheduled
            + self.pending

        )


# ==========================================================
# Service Analytics
# ==========================================================

@dataclass(slots=True)
class ServiceAnalytics:

    service_id: str

    service_name: str

    appointments: int = 0

    completed: int = 0

    cancelled: int = 0

    revenue: float = 0.0

    average_duration: float = 0.0


# ==========================================================
# Staff Analytics
# ==========================================================

@dataclass(slots=True)
class StaffAnalytics:

    employee_id: str

    employee_name: str

    appointments: int = 0

    completed: int = 0

    cancelled: int = 0

    no_show: int = 0

    utilization: float = 0.0


# ==========================================================
# Daily Analytics
# ==========================================================

@dataclass(slots=True)
class DailyAppointmentAnalytics:

    date: datetime

    appointments: int = 0

    completed: int = 0

    cancelled: int = 0

    no_show: int = 0

    revenue: float = 0.0


# ==========================================================
# Appointment Analytics Report
# ==========================================================

@dataclass(slots=True)
class AppointmentAnalyticsReport:

    report_id: str

    business_id: str

    period: AnalyticsPeriod

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    status_metrics: AppointmentStatusMetrics = field(
        default_factory=AppointmentStatusMetrics
    )

    services: list[ServiceAnalytics] = field(
        default_factory=list
    )

    staff: list[StaffAnalytics] = field(
        default_factory=list
    )

    daily: list[DailyAppointmentAnalytics] = field(
        default_factory=list
    )

    total_revenue: float = 0.0

    average_booking_rate: float = 0.0

    no_show_rate: float = 0.0

    cancellation_rate: float = 0.0

    completion_rate: float = 0.0

    metadata: dict = field(
        default_factory=dict
    )

    # ======================================================
    # Helpers
    # ======================================================

    def add_service(
        self,
        service: ServiceAnalytics,
    ):

        self.services.append(service)

    def add_staff(
        self,
        staff: StaffAnalytics,
    ):

        self.staff.append(staff)

    def add_daily_record(
        self,
        record: DailyAppointmentAnalytics,
    ):

        self.daily.append(record)

    @property
    def total_services(self) -> int:

        return len(self.services)

    @property
    def total_staff(self) -> int:

        return len(self.staff)

    @property
    def total_days(self) -> int:

        return len(self.daily)