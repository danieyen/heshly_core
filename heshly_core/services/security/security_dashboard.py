from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.services.security.security_metrics import (
    SecurityMetrics,
)
from heshly_core.services.security.security_alerts import (
    SecurityAlerts,
)
from heshly_core.services.security.intrusion_detection import (
    IntrusionDetection,
)


class SecurityDashboard:
    """
    Central security dashboard.

    Aggregates information from all
    security services into a single view.
    """

    def __init__(
        self,
        metrics: SecurityMetrics,
        alerts: SecurityAlerts,
        intrusion_detection: IntrusionDetection,
    ):

        self.metrics = metrics

        self.alerts = alerts

        self.intrusion_detection = intrusion_detection

    # =====================================================
    # Dashboard
    # =====================================================

    def summary(self) -> dict:

        metrics_snapshot = self.metrics.snapshot()

        unresolved_alerts = self.alerts.list_unresolved()

        intrusions = self.intrusion_detection.list()

        return {

            "generated_at": datetime.now(UTC),

            "metrics": metrics_snapshot,

            "alerts": {

                "total": self.alerts.count(),

                "unresolved": len(
                    unresolved_alerts
                ),

                "critical": len(
                    self.alerts.list_by_level(
                        "critical"
                    )
                ),

            },

            "intrusions": {

                "total": len(
                    intrusions
                ),

                "active": len(
                    self.intrusion_detection.unresolved()
                ),

            },

            "overall_status": self._status(),

        }

    # =====================================================
    # Status
    # =====================================================

    def _status(self) -> str:

        if len(
            self.alerts.list_by_level(
                "critical"
            )
        ) > 0:

            return "critical"

        if len(
            self.intrusion_detection.unresolved()
        ) > 0:

            return "warning"

        return "healthy"

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "security_dashboard",

            "status": "healthy",

        }