from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.services.security.security_alerts import (
    AlertLevel,
    SecurityAlert,
    SecurityAlerts,
)


class AlertManager:
    """
    Central alert management service.

    Coordinates creation, acknowledgement,
    escalation and resolution of security
    alerts generated throughout Heshly.
    """

    def __init__(
        self,
        alerts: SecurityAlerts,
    ):

        self.alerts = alerts

    # =====================================================
    # Alert Creation
    # =====================================================

    def info(
        self,
        title: str,
        message: str,
        source: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> SecurityAlert:

        return self.alerts.create_alert(

            level=AlertLevel.INFO,

            title=title,

            message=message,

            source=source,

            tenant_id=tenant_id,

            user_id=user_id,
        )

    def warning(
        self,
        title: str,
        message: str,
        source: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> SecurityAlert:

        return self.alerts.create_alert(

            level=AlertLevel.WARNING,

            title=title,

            message=message,

            source=source,

            tenant_id=tenant_id,

            user_id=user_id,
        )

    def high(
        self,
        title: str,
        message: str,
        source: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> SecurityAlert:

        return self.alerts.create_alert(

            level=AlertLevel.HIGH,

            title=title,

            message=message,

            source=source,

            tenant_id=tenant_id,

            user_id=user_id,
        )

    def critical(
        self,
        title: str,
        message: str,
        source: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> SecurityAlert:

        return self.alerts.create_alert(

            level=AlertLevel.CRITICAL,

            title=title,

            message=message,

            source=source,

            tenant_id=tenant_id,

            user_id=user_id,
        )

    # =====================================================
    # Alert Actions
    # =====================================================

    def acknowledge(
        self,
        alert_id: str,
    ) -> bool:

        return self.alerts.acknowledge(
            alert_id
        )

    def resolve(
        self,
        alert_id: str,
    ) -> bool:

        return self.alerts.resolve(
            alert_id
        )

    def escalate(
        self,
        alert_id: str,
    ) -> bool:

        alert = self.alerts.get(
            alert_id
        )

        if alert is None:

            return False

        if alert.level == AlertLevel.INFO:

            alert.level = AlertLevel.WARNING

        elif alert.level == AlertLevel.WARNING:

            alert.level = AlertLevel.HIGH

        elif alert.level == AlertLevel.HIGH:

            alert.level = AlertLevel.CRITICAL

        return True

    # =====================================================
    # Dashboard Helpers
    # =====================================================

    def active_alerts(self):

        return self.alerts.list_unresolved()

    def critical_alerts(self):

        return self.alerts.list_by_level(
            AlertLevel.CRITICAL
        )

    def summary(self):

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total": self.alerts.count(),

            "active": len(
                self.active_alerts()
            ),

            "critical": len(
                self.critical_alerts()
            ),

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "alert_manager",

            "alerts": self.alerts.count(),

            "status": "healthy",

        }