from __future__ import annotations

from datetime import datetime

from heshly_core.models.audit_log import (
    AuditEventType,
    AuditLog,
    AuditSeverity,
)


class AuditRepository:
    """
    Repository for audit log storage.

    Responsible for:
    - storing audit records
    - retrieving audit history
    - filtering audit events
    """


    def __init__(self):

        self._logs: dict[str, AuditLog] = {}


    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        audit_log: AuditLog,
    ) -> AuditLog:

        self._logs[
            audit_log.audit_id
        ] = audit_log

        return audit_log


    def get(
        self,
        audit_id: str,
    ) -> AuditLog | None:

        return self._logs.get(
            audit_id
        )


    def delete(
        self,
        audit_id: str,
    ) -> bool:

        return (

            self._logs.pop(
                audit_id,
                None,
            )

            is not None

        )


    def list(
        self,
    ) -> list[AuditLog]:

        return list(
            self._logs.values()
        )


    def count(
        self,
    ) -> int:

        return len(
            self._logs
        )


    def clear(
        self,
    ) -> None:

        self._logs.clear()


    # =====================================================
    # Tenant Queries
    # =====================================================

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[AuditLog]:

        return [

            log

            for log in self._logs.values()

            if log.tenant_id == tenant_id

        ]


    # =====================================================
    # User Queries
    # =====================================================

    def list_by_user(
        self,
        user_id: str,
    ) -> list[AuditLog]:

        return [

            log

            for log in self._logs.values()

            if log.user_id == user_id

        ]


    # =====================================================
    # Event Queries
    # =====================================================

    def list_by_event_type(
        self,
        event_type: AuditEventType,
    ) -> list[AuditLog]:

        return [

            log

            for log in self._logs.values()

            if log.event_type == event_type

        ]


    def list_security_events(
        self,
    ) -> list[AuditLog]:

        return [

            log

            for log in self._logs.values()

            if log.is_security_event

        ]


    def list_failures(
        self,
    ) -> list[AuditLog]:

        return [

            log

            for log in self._logs.values()

            if log.is_failure

        ]


    # =====================================================
    # Severity Queries
    # =====================================================

    def list_by_severity(
        self,
        severity: AuditSeverity,
    ) -> list[AuditLog]:

        return [

            log

            for log in self._logs.values()

            if log.severity == severity

        ]


    # =====================================================
    # Time Queries
    # =====================================================

    def list_between(
        self,
        start: datetime,
        end: datetime,
    ) -> list[AuditLog]:

        return [

            log

            for log in self._logs.values()

            if start <= log.created_at <= end

        ]


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "audit_repository",

            "records": self.count(),

            "status": "healthy",

        }