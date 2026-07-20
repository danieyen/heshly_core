from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from heshly_core.services.security.alert_manager import (
    AlertManager,
)
from heshly_core.services.security.intrusion_detection import (
    IntrusionDetection,
)
from heshly_core.services.security.security_metrics import (
    SecurityMetrics,
)


# =====================================================
# Incident Status
# =====================================================

class IncidentStatus:

    OPEN = "open"

    INVESTIGATING = "investigating"

    RESOLVED = "resolved"

    CLOSED = "closed"


# =====================================================
# Incident Report
# =====================================================

@dataclass(slots=True)
class IncidentReport:

    incident_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    title: str = ""

    description: str = ""

    severity: str = "medium"

    tenant_id: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    status: str = IncidentStatus.OPEN

    alerts: int = 0

    intrusions: int = 0

    metrics: dict = field(
        default_factory=dict
    )

    recommendations: list[str] = field(
        default_factory=list
    )


# =====================================================
# Incident Reporting
# =====================================================

class IncidentReporting:
    """
    Produces security incident reports from
    the monitoring subsystem.
    """

    def __init__(

        self,

        metrics: SecurityMetrics,

        intrusion_detection: IntrusionDetection,

        alert_manager: AlertManager,

    ):

        self.metrics = metrics

        self.intrusion_detection = intrusion_detection

        self.alert_manager = alert_manager

        self._reports: dict[
            str,
            IncidentReport,
        ] = {}

    # =====================================================
    # Report Generation
    # =====================================================

    def create_report(

        self,

        title: str,

        description: str,

        severity: str = "medium",

        tenant_id: str | None = None,

    ) -> IncidentReport:

        report = IncidentReport(

            title=title,

            description=description,

            severity=severity,

            tenant_id=tenant_id,

            alerts=self.alert_manager.summary()[
                "total"
            ],

            intrusions=self.intrusion_detection.count(),

            metrics=self.metrics.snapshot(),

        )

        report.recommendations = self._recommendations(
            report
        )

        self._reports[
            report.incident_id
        ] = report

        return report

    # =====================================================
    # Recommendations
    # =====================================================

    def _recommendations(

        self,

        report: IncidentReport,

    ) -> list[str]:

        recommendations = []

        if report.intrusions:

            recommendations.append(
                "Investigate intrusion attempts."
            )

        if report.alerts:

            recommendations.append(
                "Review unresolved security alerts."
            )

        if report.metrics.get(
            "failed_logins",
            0,
        ) > 10:

            recommendations.append(
                "Review authentication logs."
            )

        if not recommendations:

            recommendations.append(
                "No immediate action required."
            )

        return recommendations

    # =====================================================
    # Queries
    # =====================================================

    def get(

        self,

        incident_id: str,

    ) -> IncidentReport | None:

        return self._reports.get(
            incident_id
        )

    def list(self):

        return list(
            self._reports.values()
        )

    def count(self):

        return len(
            self._reports
        )

    # =====================================================
    # Status
    # =====================================================

    def update_status(

        self,

        incident_id: str,

        status: str,

    ) -> bool:

        report = self.get(
            incident_id
        )

        if report is None:

            return False

        report.status = status

        return True

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "incident_reporting",

            "reports": self.count(),

            "status": "healthy",

        }