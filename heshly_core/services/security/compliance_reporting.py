from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from heshly_core.repositories.audit_repository import (
    AuditRepository,
)


class ComplianceReporting:
    """
    Generates compliance and audit reports.

    Reports can be used for:
    - Internal audits
    - Security reviews
    - Compliance reporting
    """

    def __init__(
        self,
        repository: AuditRepository,
    ):

        self.repository = repository

    # =====================================================
    # Report
    # =====================================================

    def generate_report(
        self,
        tenant_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict:

        logs = self.repository.list()

        if tenant_id is not None:

            logs = [

                log

                for log in logs

                if log.tenant_id == tenant_id

            ]

        if start is not None:

            logs = [

                log

                for log in logs

                if log.created_at >= start

            ]

        if end is not None:

            logs = [

                log

                for log in logs

                if log.created_at <= end

            ]

        event_counts = Counter(
            log.event_type.value
            for log in logs
        )

        severity_counts = Counter(
            log.severity.value
            for log in logs
        )

        security_events = sum(
            1
            for log in logs
            if log.is_security_event
        )

        failed_events = sum(
            1
            for log in logs
            if log.is_failure
        )

        return {

            "tenant_id": tenant_id,

            "generated_at": datetime.now(UTC),

            "total_events": len(logs),

            "security_events": security_events,

            "failed_events": failed_events,

            "events": dict(event_counts),

            "severity": dict(severity_counts),

        }

    # =====================================================
    # Helpers
    # =====================================================

    def has_security_events(
        self,
        tenant_id: str | None = None,
    ) -> bool:

        report = self.generate_report(
            tenant_id=tenant_id
        )

        return report["security_events"] > 0

    def has_failures(
        self,
        tenant_id: str | None = None,
    ) -> bool:

        report = self.generate_report(
            tenant_id=tenant_id
        )

        return report["failed_events"] > 0

    def summary(
        self,
        tenant_id: str | None = None,
    ) -> dict:

        report = self.generate_report(
            tenant_id=tenant_id
        )

        return {

            "tenant_id": report["tenant_id"],

            "total_events": report["total_events"],

            "security_events": report["security_events"],

            "failed_events": report["failed_events"],

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "compliance_reporting",

            "audit_records": self.repository.count(),

            "status": "healthy",

        }