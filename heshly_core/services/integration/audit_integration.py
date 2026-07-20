from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AuditResult:
    """
    Result returned from audit operations.
    """

    success: bool

    event_id: str | None = None

    message: str | None = None



class AuditIntegration:
    """
    High-level audit orchestration layer.

    Connects:
    - Audit Service
    - Activity Tracking
    - Compliance Reporting
    - Security Monitoring
    """

    def __init__(
        self,
        audit_service,
        activity_tracker,
        compliance_reporting,
        security_metrics,
        security_alerts,
    ):

        self.audit_service = audit_service

        self.activity_tracker = activity_tracker

        self.compliance_reporting = (
            compliance_reporting
        )

        self.security_metrics = security_metrics

        self.security_alerts = security_alerts


    # =====================================================
    # Authentication Events
    # =====================================================

    def record_login(
        self,
        tenant_id: str,
        user_id: str,
    ):

        event = self.audit_service.login(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        self.security_metrics.increment(
            "audit_login_events"
        )

        return AuditResult(

            success=True,

            event_id=getattr(
                event,
                "id",
                None,
            ),

            message="Login audited",

        )


    def record_logout(
        self,
        tenant_id: str,
        user_id: str,
    ):

        event = self.audit_service.logout(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        self.security_metrics.increment(
            "audit_logout_events"
        )

        return AuditResult(

            success=True,

            event_id=getattr(
                event,
                "id",
                None,
            ),

            message="Logout audited",

        )


    # =====================================================
    # Business Activity
    # =====================================================

    def track_activity(
        self,
        activity: str,
        tenant_id: str,
        user_id: str,
        reference_id: str,
    ):

        handler = getattr(
            self.activity_tracker,
            activity,
        )

        result = handler(
            tenant_id,
            user_id,
            reference_id,
        )

        self.security_metrics.increment(
            "business_audit_events"
        )

        return AuditResult(

            success=True,

            event_id=getattr(
                result,
                "id",
                None,
            ),

            message="Activity tracked",

        )


    # =====================================================
    # Security Events
    # =====================================================

    def record_security_event(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        description: str,
    ):

        event = self.audit_service.security_event(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            description=description,
        )

        self.security_alerts.create(
            action,
            description,
        )

        self.security_metrics.increment(
            "security_events"
        )

        return AuditResult(

            success=True,

            event_id=getattr(
                event,
                "id",
                None,
            ),

            message="Security event recorded",

        )


    # =====================================================
    # Compliance
    # =====================================================

    def compliance_report(
        self,
        tenant_id: str,
    ):

        return self.compliance_reporting.generate_report(
            tenant_id
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "audit_integration",

            "status": "healthy",

        }