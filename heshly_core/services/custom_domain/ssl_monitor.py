from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone

import frappe


class SSLCertificateMonitor:
    """
    Checks the public TLS certificate for a custom domain.

    This service performs certificate inspection only.
    Certificate issuance/renewal is handled separately.
    """

    EXPIRING_DAYS = 30
    CONNECT_TIMEOUT = 10

    DOCTYPE = "Custom Domain"

    # =====================================================
    # Check Certificate
    # =====================================================

    def check(self, domain: str) -> dict:
        domain = self._normalize_domain(domain)

        checked_at = frappe.utils.now_datetime()

        try:
            certificate = self._get_certificate(domain)

            expires_at = self._parse_expiry(
                certificate["notAfter"]
            )

            now = datetime.now(timezone.utc)

            days_remaining = (
                expires_at - now
            ).total_seconds() / 86400

            days_remaining_int = int(days_remaining)

            if days_remaining <= 0:
                status = "Expired"
            elif days_remaining <= self.EXPIRING_DAYS:
                status = "Expiring"
            else:
                status = "Healthy"

            result = {
                "domain": domain,
                "status": status,
                "ssl_last_checked": checked_at,
                "ssl_expires_at": expires_at,
                "ssl_days_remaining": days_remaining_int,
                "ssl_last_error": None,
            }

        except Exception as exc:
            result = {
                "domain": domain,
                "status": "Failed",
                "ssl_last_checked": checked_at,
                "ssl_expires_at": None,
                "ssl_days_remaining": None,
                "ssl_last_error": str(exc),
            }

        self._persist(result)

        return result

    # =====================================================
    # Certificate Connection
    # =====================================================

    def _get_certificate(self, domain: str) -> dict:
        context = ssl.create_default_context()

        with socket.create_connection(
            (domain, 443),
            timeout=self.CONNECT_TIMEOUT,
        ) as sock:

            with context.wrap_socket(
                sock,
                server_hostname=domain,
            ) as tls_socket:

                return tls_socket.getpeercert()

    # =====================================================
    # Expiry Parsing
    # =====================================================

    @staticmethod
    def _parse_expiry(value: str) -> datetime:
        expiry = datetime.strptime(
            value,
            "%b %d %H:%M:%S %Y %Z",
        )

        return expiry.replace(
            tzinfo=timezone.utc
        )

    # =====================================================
    # Persist
    # =====================================================

    def _persist(self, result: dict) -> None:
        domain = result["domain"]

        name = frappe.db.get_value(
            self.DOCTYPE,
            {"domain": domain},
            "name",
        )

        if not name:
            return

        values = {
            "ssl_last_checked": result[
                "ssl_last_checked"
            ],
            "ssl_expires_at": result[
                "ssl_expires_at"
            ],
            "ssl_days_remaining": result[
                "ssl_days_remaining"
            ],
            "ssl_last_error": result[
                "ssl_last_error"
            ],
            "ssl_check_status": result[
                "status"
            ],
        }

        frappe.db.set_value(
            self.DOCTYPE,
            name,
            values,
            update_modified=False,
        )

        frappe.db.commit()

    # =====================================================
    # Normalization
    # =====================================================

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        domain = (
            domain
            .strip()
            .lower()
            .rstrip(".")
        )

        if not domain:
            raise ValueError(
                "Domain is required."
            )

        return domain
