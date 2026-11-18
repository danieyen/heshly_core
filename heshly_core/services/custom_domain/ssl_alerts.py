from __future__ import annotations

import frappe


class SSLAlertService:
    """
    Sends and records alerts for SSL certificate problems.

    Email delivery is optional. If no outgoing Email Account
    is configured, the alert is still persisted in Error Log.
    """

    ALERT_STATUSES = {
        "Expiring",
        "Expired",
        "Failed",
    }

    def process(self, result: dict) -> dict:
        domain = result["domain"]
        status = result["status"]

        if status not in self.ALERT_STATUSES:
            return {
                "alerted": False,
                "reason": "No alert required.",
            }

        subject = self._subject(result)
        message = self._message(result)

        # Always persist the operational alert.
        frappe.log_error(
            title=subject,
            message=message,
        )

        recipient = self._get_recipient()

        if not recipient:
            return {
                "alerted": True,
                "email_sent": False,
                "reason": "No outgoing Email Account configured.",
            }

        try:
            frappe.sendmail(
                recipients=[recipient],
                subject=subject,
                message=message,
            )

            return {
                "alerted": True,
                "email_sent": True,
                "recipient": recipient,
            }

        except Exception:
            frappe.log_error(
                title=f"SSL alert email failed: {domain}",
                message=frappe.get_traceback(),
            )

            return {
                "alerted": True,
                "email_sent": False,
                "reason": "Email delivery failed.",
            }

    # =====================================================
    # Recipient
    # =====================================================

    @staticmethod
    def _get_recipient() -> str | None:
        account = frappe.db.get_value(
            "Email Account",
            {
                "enable_outgoing": 1,
                "default_outgoing": 1,
            },
            "email_id",
        )

        if account:
            return account

        account = frappe.db.get_value(
            "Email Account",
            {
                "enable_outgoing": 1,
            },
            "email_id",
        )

        return account or None

    # =====================================================
    # Subject
    # =====================================================

    @staticmethod
    def _subject(result: dict) -> str:
        domain = result["domain"]
        status = result["status"]

        return (
            f"[Heshly SSL Alert] "
            f"{domain}: {status}"
        )

    # =====================================================
    # Message
    # =====================================================

    @staticmethod
    def _message(result: dict) -> str:
        domain = result["domain"]
        status = result["status"]
        days = result.get("ssl_days_remaining")
        expires = result.get("ssl_expires_at")
        error = result.get("ssl_last_error")

        lines = [
            "Heshly SSL Certificate Alert",
            "",
            f"Domain: {domain}",
            f"Status: {status}",
            f"Days remaining: {days}",
            f"Expires at: {expires}",
        ]

        if error:
            lines.extend(
                [
                    "",
                    "Error:",
                    str(error),
                ]
            )

        return "\n".join(lines)
