from __future__ import annotations

from datetime import timedelta

import frappe

from heshly_core.services.custom_domain.ssl_monitor import (
    SSLCertificateMonitor,
)


class SSLRetryService:
    """
    Handles retries for failed SSL certificate checks.

    Retry delays:
        1 -> 5 minutes
        2 -> 15 minutes
        3 -> 30 minutes
        4 -> 60 minutes
        5 -> 120 minutes

    After MAX_RETRIES, no further automatic retries are scheduled.
    """

    MAX_RETRIES = 5

    RETRY_DELAYS = {
        1: 5,
        2: 15,
        3: 30,
        4: 60,
        5: 120,
    }

    def __init__(self):
        self.monitor = SSLCertificateMonitor()

    # =====================================================
    # Process One Domain
    # =====================================================

    def process(self, domain: str) -> dict:
        record = frappe.db.get_value(
            "Custom Domain",
            {"domain": domain},
            [
                "name",
                "domain",
                "active",
                "verified",
                "ssl_enabled",
                "ssl_retry_count",
                "ssl_next_retry_at",
            ],
            as_dict=True,
        )

        if not record:
            return {
                "status": "skipped",
                "reason": "Domain not found.",
                "domain": domain,
            }

        if not record.active:
            return {
                "status": "skipped",
                "reason": "Domain inactive.",
                "domain": domain,
            }

        if not record.verified:
            return {
                "status": "skipped",
                "reason": "Domain not verified.",
                "domain": domain,
            }

        if not record.ssl_enabled:
            return {
                "status": "skipped",
                "reason": "SSL is not enabled.",
                "domain": domain,
            }

        retry_count = int(record.ssl_retry_count or 0)

        now = frappe.utils.now_datetime()

        if record.ssl_next_retry_at:
            if now < record.ssl_next_retry_at:
                return {
                    "status": "waiting",
                    "domain": domain,
                    "retry_count": retry_count,
                    "next_retry_at": record.ssl_next_retry_at,
                }

        if retry_count >= self.MAX_RETRIES:
            return {
                "status": "exhausted",
                "domain": domain,
                "retry_count": retry_count,
            }

        result = self.monitor.check(domain)

        if result["status"] != "Failed":
            self._reset_retry_state(record.name)

            return {
                "status": "success",
                "domain": domain,
                "certificate_status": result["status"],
                "retry_count": retry_count,
            }

        next_retry_count = retry_count + 1

        if next_retry_count > self.MAX_RETRIES:
            self._mark_exhausted(
                record.name,
                result.get("ssl_last_error"),
            )

            return {
                "status": "exhausted",
                "domain": domain,
                "retry_count": retry_count,
                "error": result.get("ssl_last_error"),
            }

        delay_minutes = self.RETRY_DELAYS[
            next_retry_count
        ]

        next_retry_at = (
            now + timedelta(minutes=delay_minutes)
        )

        self._schedule_retry(
            name=record.name,
            retry_count=next_retry_count,
            next_retry_at=next_retry_at,
            error=result.get("ssl_last_error"),
        )

        return {
            "status": "retry_scheduled",
            "domain": domain,
            "retry_count": next_retry_count,
            "next_retry_at": next_retry_at,
            "delay_minutes": delay_minutes,
            "error": result.get("ssl_last_error"),
        }

    # =====================================================
    # Reset
    # =====================================================

    @staticmethod
    def _reset_retry_state(name: str) -> None:
        frappe.db.set_value(
            "Custom Domain",
            name,
            {
                "ssl_retry_count": 0,
                "ssl_next_retry_at": None,
                "ssl_last_error": None,
            },
            update_modified=False,
        )

        frappe.db.commit()

    # =====================================================
    # Schedule Retry
    # =====================================================

    @staticmethod
    def _schedule_retry(
        name: str,
        retry_count: int,
        next_retry_at,
        error: str | None,
    ) -> None:

        frappe.db.set_value(
            "Custom Domain",
            name,
            {
                "ssl_retry_count": retry_count,
                "ssl_next_retry_at": next_retry_at,
                "ssl_last_error": error,
            },
            update_modified=False,
        )

        frappe.db.commit()

    # =====================================================
    # Exhausted
    # =====================================================

    @staticmethod
    def _mark_exhausted(
        name: str,
        error: str | None,
    ) -> None:

        frappe.db.set_value(
            "Custom Domain",
            name,
            {
                "ssl_retry_count": SSLRetryService.MAX_RETRIES,
                "ssl_next_retry_at": None,
                "ssl_last_error": error,
            },
            update_modified=False,
        )

        frappe.db.commit()

        frappe.log_error(
            title="SSL retry limit exhausted",
            message=(
                f"Custom Domain: {name}\n"
                f"Retry limit: "
                f"{SSLRetryService.MAX_RETRIES}\n"
                f"Error: {error or 'Unknown error'}"
            ),
        )
