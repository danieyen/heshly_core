from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


# =====================================================
# Alert Levels
# =====================================================

class AlertLevel:

    INFO = "info"

    WARNING = "warning"

    HIGH = "high"

    CRITICAL = "critical"


# =====================================================
# Security Alert
# =====================================================

@dataclass(slots=True)
class SecurityAlert:

    alert_id: str

    tenant_id: str | None

    user_id: str | None

    level: str

    title: str

    message: str

    source: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    acknowledged: bool = False

    resolved: bool = False


# =====================================================
# Security Alerts
# =====================================================

class SecurityAlerts:
    """
    Central manager for security alerts.

    Used by:
    - Brute Force Protection
    - Suspicious Activity Detection
    - API Security
    - Authentication
    - Audit & Compliance
    """

    def __init__(self):

        self._alerts: dict[
            str,
            SecurityAlert,
        ] = {}

    # =====================================================
    # Create
    # =====================================================

    def create_alert(

        self,

        level: str,

        title: str,

        message: str,

        source: str,

        tenant_id: str | None = None,

        user_id: str | None = None,

    ) -> SecurityAlert:

        alert = SecurityAlert(

            alert_id=str(
                uuid4()
            ),

            tenant_id=tenant_id,

            user_id=user_id,

            level=level,

            title=title,

            message=message,

            source=source,

        )

        self._alerts[
            alert.alert_id
        ] = alert

        return alert

    # =====================================================
    # Queries
    # =====================================================

    def get(

        self,

        alert_id: str,

    ) -> SecurityAlert | None:

        return self._alerts.get(
            alert_id
        )

    def list(self):

        return list(
            self._alerts.values()
        )

    def list_unresolved(self):

        return [

            alert

            for alert in self._alerts.values()

            if not alert.resolved

        ]

    def list_by_level(

        self,

        level: str,

    ):

        return [

            alert

            for alert in self._alerts.values()

            if alert.level == level

        ]

    # =====================================================
    # Status
    # =====================================================

    def acknowledge(

        self,

        alert_id: str,

    ) -> bool:

        alert = self.get(
            alert_id
        )

        if alert is None:

            return False

        alert.acknowledged = True

        return True

    def resolve(

        self,

        alert_id: str,

    ) -> bool:

        alert = self.get(
            alert_id
        )

        if alert is None:

            return False

        alert.resolved = True

        return True

    # =====================================================
    # Management
    # =====================================================

    def delete(

        self,

        alert_id: str,

    ) -> bool:

        return (

            self._alerts.pop(
                alert_id,
                None,
            )

            is not None

        )

    def clear(self):

        self._alerts.clear()

    def count(self):

        return len(
            self._alerts
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "security_alerts",

            "alerts": self.count(),

            "unresolved": len(
                self.list_unresolved()
            ),

            "status": "healthy",

        }