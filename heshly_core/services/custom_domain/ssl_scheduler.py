from __future__ import annotations

import frappe

from datetime import timedelta

from heshly_core.services.custom_domain.ssl_alerts import (
    SSLAlertService,
)
from heshly_core.services.custom_domain.ssl_retry import (
    SSLRetryService,
)


def check_all_custom_domain_ssl() -> None:
    """
    Hourly SSL monitoring and retry processing.
    """

    retry_service = SSLRetryService()
    alerts = SSLAlertService()

    domains = frappe.get_all(
        "Custom Domain",
        filters={
            "active": 1,
            "verified": 1,
            "ssl_enabled": 1,
        },
        fields=["name", "domain"],
    )

    checked = 0
    retries = 0
    exhausted = 0
    alerted = 0

    for record in domains:
        try:
            result = retry_service.process(
                record.domain
            )

            checked += 1

            if result["status"] == "retry_scheduled":
                retries += 1

            elif result["status"] == "exhausted":
                exhausted += 1

                alerts.process({
                    "domain": record.domain,
                    "status": "Failed",
                    "ssl_days_remaining": None,
                    "ssl_expires_at": None,
                    "ssl_last_error": result.get("error"),
                })

                alerted += 1

            elif result["status"] == "success":
                certificate_status = result[
                    "certificate_status"
                ]

                if certificate_status in {
                    "Expiring",
                    "Expired",
                }:
                    alert_result = alerts.process({
                        "domain": record.domain,
                        "status": certificate_status,
                        "ssl_days_remaining": None,
                        "ssl_expires_at": None,
                        "ssl_last_error": None,
                    })

                    if alert_result["alerted"]:
                        alerted += 1

        except Exception:
            frappe.log_error(
                title=f"SSL scheduler exception: {record.domain}",
                message=frappe.get_traceback(),
            )

    summary = {
        "checked": checked,
        "retries": retries,
        "exhausted": exhausted,
        "alerted": alerted,
    }

    frappe.logger(
        "heshly_core.ssl_monitor"
    ).info(
        "SSL monitoring completed: %s",
        summary,
    )

    return summary

    return {
        "checked": checked,
        "retries": retries,
        "exhausted": exhausted,
        "alerted": alerted,
    }