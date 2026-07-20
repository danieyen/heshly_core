from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from heshly_core.models.audit_log import (
    AuditEventType,
    AuditLog,
    AuditSeverity,
)
from heshly_core.repositories.audit_repository import (
    AuditRepository,
)


class AuditService:
    """
    Central audit logging service.

    Responsible for recording all
    security, user, and system events.
    """

    def __init__(
        self,
        repository: AuditRepository,
    ):

        self.repository = repository

    # =====================================================
    # Log Event
    # =====================================================

    def log(
        self,
        *,
        tenant_id: str | None,
        user_id: str | None,
        event_type: AuditEventType,
        action: str,
        resource: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        description: str = "",
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:

        audit = AuditLog(

            audit_id=str(
                uuid4()
            ),

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=event_type,

            action=action,

            resource=resource,

            severity=severity,

            description=description,

            ip_address=ip_address,

            user_agent=user_agent,

            metadata=metadata or {},

            created_at=datetime.now(
                UTC
            ),

        )

        self.repository.save(
            audit
        )

        return audit

    # =====================================================
    # Convenience Methods
    # =====================================================

    def login(
        self,
        tenant_id: str,
        user_id: str,
        ip_address: str | None = None,
    ) -> AuditLog:

        return self.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.LOGIN,

            action="login",

            resource="authentication",

            description="User logged in",

            ip_address=ip_address,

        )

    def logout(
        self,
        tenant_id: str,
        user_id: str,
    ) -> AuditLog:

        return self.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.LOGOUT,

            action="logout",

            resource="authentication",

            description="User logged out",

        )

    def access_denied(
        self,
        tenant_id: str,
        user_id: str,
        resource: str,
    ) -> AuditLog:

        return self.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.ACCESS_DENIED,

            action="access_denied",

            resource=resource,

            severity=AuditSeverity.WARNING,

            description="Permission denied",

        )

    def security_event(
        self,
        tenant_id: str | None,
        user_id: str | None,
        action: str,
        description: str,
    ) -> AuditLog:

        return self.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.SECURITY,

            action=action,

            resource="security",

            severity=AuditSeverity.CRITICAL,

            description=description,

        )

    # =====================================================
    # Queries
    # =====================================================

    def history(
        self,
    ) -> list[AuditLog]:

        return self.repository.list()

    def tenant_history(
        self,
        tenant_id: str,
    ) -> list[AuditLog]:

        return self.repository.list_by_tenant(
            tenant_id
        )

    def user_history(
        self,
        user_id: str,
    ) -> list[AuditLog]:

        return self.repository.list_by_user(
            user_id
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "audit_service",

            "records": self.repository.count(),

            "status": "healthy",

        }