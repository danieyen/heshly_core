from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from statistics import mean


class RevenueAnalytics:
    """
    Revenue Analytics

    Expected sale format

    {
        "sale_id": "...",
        "customer_id": "...",
        "customer_name": "...",
        "employee_name": "...",
        "service_name": "...",
        "amount": 4500,
        "discount": 500,
        "tax": 240,
        "total": 4240,
        "payment_method": "Cash",
        "status": "completed",
        "sale_date": datetime(...)
    }
    """

    # =====================================================
    # Revenue Analysis
    # =====================================================

    def analyze(
        self,
        sales: list[dict],
    ) -> dict:

        completed_sales = []

        payment_breakdown = defaultdict(float)
        service_breakdown = defaultdict(float)
        employee_breakdown = defaultdict(float)
        monthly_breakdown = defaultdict(float)

        total_amount = 0.0
        total_discount = 0.0
        total_tax = 0.0
        total_revenue = 0.0

        for sale in sales:

            if sale.get("status", "").lower() != "completed":
                continue

            amount = float(
                sale.get("amount", 0)
            )

            discount = float(
                sale.get("discount", 0)
            )

            tax = float(
                sale.get("tax", 0)
            )

            total = float(
                sale.get(
                    "total",
                    amount - discount + tax,
                )
            )

            total_amount += amount
            total_discount += discount
            total_tax += tax
            total_revenue += total

            completed_sales.append(total)

            payment = sale.get(
                "payment_method",
                "Unknown",
            )

            payment_breakdown[payment] += total

            service = sale.get(
                "service_name",
                "Unknown",
            )

            service_breakdown[service] += total

            employee = sale.get(
                "employee_name",
                "Unknown",
            )

            employee_breakdown[employee] += total

            sale_date = sale.get("sale_date")

            if isinstance(sale_date, datetime):

                month = sale_date.strftime(
                    "%Y-%m"
                )

                monthly_breakdown[month] += total

        total_sales = len(completed_sales)

        average_sale = (
            round(
                mean(completed_sales),
                2,
            )
            if completed_sales
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_sales": total_sales,

            "gross_revenue": round(
                total_amount,
                2,
            ),

            "discounts": round(
                total_discount,
                2,
            ),

            "tax": round(
                total_tax,
                2,
            ),

            "net_revenue": round(
                total_revenue,
                2,
            ),

            "average_sale": average_sale,

            "highest_sale": (
                max(completed_sales)
                if completed_sales
                else 0.0
            ),

            "lowest_sale": (
                min(completed_sales)
                if completed_sales
                else 0.0
            ),

            "payment_breakdown": dict(
                payment_breakdown
            ),

            "service_breakdown": dict(
                service_breakdown
            ),

            "employee_breakdown": dict(
                employee_breakdown
            ),

            "monthly_breakdown": dict(
                monthly_breakdown
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_services(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "service_breakdown"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def top_employees(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "employee_breakdown"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def payment_methods(
        self,
        report: dict,
    ):

        return sorted(

            report[
                "payment_breakdown"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ):

        return {

            "sales": report[
                "total_sales"
            ],

            "gross_revenue": report[
                "gross_revenue"
            ],

            "net_revenue": report[
                "net_revenue"
            ],

            "average_sale": report[
                "average_sale"
            ],

            "highest_sale": report[
                "highest_sale"
            ],

            "top_service": self.top_services(
                report,
                1,
            ),

            "top_employee": self.top_employees(
                report,
                1,
            ),

            "top_payment_method": self.payment_methods(
                report,
            )[:1],

        }