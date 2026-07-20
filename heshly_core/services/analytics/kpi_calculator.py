from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.analytics import (
    KPI,
    TimePeriod,
)


class KPICalculator:
    """
    KPI Calculator

    Calculates and manages business KPIs.

    Supported KPIs

        • Revenue
        • Growth
        • Conversion Rate
        • Appointment Rate
        • No-show Rate
        • Customer Retention
        • Customer Satisfaction
        • Average Deal Size
        • Win Rate
        • Pipeline Velocity
        • AI Accuracy
    """

    def __init__(self):

        self._kpis: dict[str, KPI] = {}

    # =====================================================
    # KPI Management
    # =====================================================

    def register(
        self,
        kpi: KPI,
    ) -> KPI:

        self._kpis[kpi.kpi_id] = kpi

        return kpi

    def get(
        self,
        kpi_id: str,
    ) -> KPI | None:

        return self._kpis.get(kpi_id)

    def all(self) -> list[KPI]:

        return list(self._kpis.values())

    def delete(
        self,
        kpi_id: str,
    ) -> bool:

        return self._kpis.pop(
            kpi_id,
            None,
        ) is not None

    def clear(self):

        self._kpis.clear()

    # =====================================================
    # Generic KPI
    # =====================================================

    def create(
        self,
        kpi_id: str,
        name: str,
        value: float,
        target: float = 0.0,
        unit: str = "",
        trend: float = 0.0,
        period: TimePeriod = TimePeriod.MONTH,
        description: str = "",
    ) -> KPI:

        kpi = KPI(

            kpi_id=kpi_id,

            name=name,

            value=value,

            target=target,

            unit=unit,

            trend=trend,

            period=period,

            description=description,

            created_at=datetime.now(UTC),

        )

        return self.register(kpi)

    # =====================================================
    # KPI Calculations
    # =====================================================

    def revenue_kpi(
        self,
        revenue: float,
        target: float,
    ) -> KPI:

        trend = 0.0

        if target > 0:

            trend = (revenue / target) * 100

        return self.create(

            kpi_id="revenue",

            name="Revenue",

            value=revenue,

            target=target,

            unit="KES",

            trend=round(trend, 2),

        )

    def conversion_rate(

        self,

        converted: int,

        total: int,

    ) -> KPI:

        rate = 0.0

        if total > 0:

            rate = (converted / total) * 100

        return self.create(

            kpi_id="conversion_rate",

            name="Conversion Rate",

            value=round(rate, 2),

            target=50,

            unit="%",

        )

    def appointment_rate(

        self,

        booked: int,

        enquiries: int,

    ) -> KPI:

        value = 0.0

        if enquiries > 0:

            value = (booked / enquiries) * 100

        return self.create(

            "appointment_rate",

            "Appointment Rate",

            round(value, 2),

            70,

            "%",

        )

    def win_rate(

        self,

        won: int,

        total: int,

    ) -> KPI:

        value = 0.0

        if total > 0:

            value = (won / total) * 100

        return self.create(

            "win_rate",

            "Win Rate",

            round(value, 2),

            40,

            "%",

        )

    def no_show_rate(

        self,

        missed: int,

        booked: int,

    ) -> KPI:

        value = 0.0

        if booked > 0:

            value = (missed / booked) * 100

        return self.create(

            "no_show_rate",

            "No-show Rate",

            round(value, 2),

            5,

            "%",

        )

    def customer_retention(

        self,

        retained: int,

        customers: int,

    ) -> KPI:

        value = 0.0

        if customers > 0:

            value = (retained / customers) * 100

        return self.create(

            "customer_retention",

            "Customer Retention",

            round(value, 2),

            80,

            "%",

        )

    def average_sale(

        self,

        revenue: float,

        sales: int,

    ) -> KPI:

        value = 0.0

        if sales > 0:

            value = revenue / sales

        return self.create(

            "average_sale",

            "Average Sale",

            round(value, 2),

            0,

            "KES",

        )

    def ai_accuracy(

        self,

        correct: int,

        total: int,

    ) -> KPI:

        value = 0.0

        if total > 0:

            value = (correct / total) * 100

        return self.create(

            "ai_accuracy",

            "AI Accuracy",

            round(value, 2),

            95,

            "%",

        )

    # =====================================================
    # Helpers
    # =====================================================

    def achieved(
        self,
        kpi: KPI,
    ) -> bool:

        return kpi.value >= kpi.target

    def achievement_percentage(
        self,
        kpi: KPI,
    ) -> float:

        if kpi.target <= 0:

            return 0.0

        return round(

            (kpi.value / kpi.target) * 100,

            2,

        )

    # =====================================================
    # Summary
    # =====================================================

    def summary(self) -> dict:

        achieved = sum(

            1

            for kpi in self._kpis.values()

            if self.achieved(kpi)

        )

        return {

            "total_kpis": len(self._kpis),

            "achieved": achieved,

            "not_achieved": (

                len(self._kpis)

                - achieved

            ),

        }