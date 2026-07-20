from __future__ import annotations

from heshly_core.models.audit_log import (
    AuditEventType,
    AuditLog,
    AuditSeverity,
)
from heshly_core.services.security.audit_service import (
    AuditService,
)


class ActivityTracker:
    """
    Tracks user and system activities.

    Provides a higher-level API over the
    AuditService for common business
    activities.
    """

    def __init__(
        self,
        audit_service: AuditService,
    ):

        self.audit_service = audit_service

    # =====================================================
    # Customer
    # =====================================================

    def customer_created(
        self,
        tenant_id: str,
        user_id: str,
        customer_id: str,
    ) -> AuditLog:

        return self.audit_service.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.CREATE,

            action="create_customer",

            resource="customer",

            description=f"Customer {customer_id} created",

            metadata={
                "customer_id": customer_id,
            },

        )

    def customer_updated(
        self,
        tenant_id: str,
        user_id: str,
        customer_id: str,
    ) -> AuditLog:

        return self.audit_service.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.UPDATE,

            action="update_customer",

            resource="customer",

            description=f"Customer {customer_id} updated",

            metadata={
                "customer_id": customer_id,
            },

        )

    # =====================================================
    # Appointment
    # =====================================================

    def appointment_booked(
        self,
        tenant_id: str,
        user_id: str,
        appointment_id: str,
    ) -> AuditLog:

        return self.audit_service.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.CREATE,

            action="book_appointment",

            resource="appointment",

            description=f"Appointment {appointment_id} booked",

            metadata={
                "appointment_id": appointment_id,
            },

        )

    # =====================================================
    # Lead
    # =====================================================

    def lead_created(
        self,
        tenant_id: str,
        user_id: str,
        lead_id: str,
    ) -> AuditLog:

        return self.audit_service.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.CREATE,

            action="create_lead",

            resource="lead",

            description=f"Lead {lead_id} created",

            metadata={
                "lead_id": lead_id,
            },

        )

    # =====================================================
    # AI
    # =====================================================

    def ai_conversation(
        self,
        tenant_id: str,
        session_id: str,
    ) -> AuditLog:

        return self.audit_service.log(

            tenant_id=tenant_id,

            user_id=None,

            event_type=AuditEventType.SYSTEM,

            action="ai_conversation",

            resource="ai",

            description=f"AI session {session_id}",

            metadata={
                "session_id": session_id,
            },

        )

    # =====================================================
    # Security
    # =====================================================

    def suspicious_activity(
        self,
        tenant_id: str,
        user_id: str | None,
        description: str,
    ) -> AuditLog:

        return self.audit_service.log(

            tenant_id=tenant_id,

            user_id=user_id,

            event_type=AuditEventType.SECURITY,

            action="suspicious_activity",

            resource="security",

            severity=AuditSeverity.CRITICAL,

            description=description,

        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "activity_tracker",

            "records": len(
                self.audit_service.history()
            ),

            "status": "healthy",

        }