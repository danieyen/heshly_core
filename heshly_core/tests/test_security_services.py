from heshly_core.services.integration.security_services import SecurityServices

from heshly_core.services.auth.authentication_service import AuthenticationService
from heshly_core.services.auth.authorization_manager import AuthorizationManager
from heshly_core.services.auth.session_manager import SessionManager

from heshly_core.services.security.token_manager import TokenManager
from heshly_core.services.security.jwt_manager import JWTManager
from heshly_core.services.security.refresh_token_manager import RefreshTokenManager
from heshly_core.services.security.token_revocation import TokenRevocation

from heshly_core.services.security.encryption_service import EncryptionService
from heshly_core.services.security.secret_manager import SecretManager
from heshly_core.services.security.secure_configuration import SecureConfiguration
from heshly_core.services.security.data_masking import DataMasking
from heshly_core.services.security.sensitive_data_protection import (
    SensitiveDataProtection,
)

from heshly_core.repositories.audit_repository import AuditRepository

from heshly_core.services.security.audit_service import AuditService
from heshly_core.services.security.activity_tracker import ActivityTracker
from heshly_core.services.security.compliance_reporting import ComplianceReporting

from heshly_core.services.security.brute_force_protection import BruteForceProtection
from heshly_core.services.security.account_lockout import AccountLockout
from heshly_core.services.security.suspicious_activity_detection import (
    SuspiciousActivityDetection,
)
from heshly_core.services.security.ip_access_control import IPAccessControl

from heshly_core.services.security.security_alerts import SecurityAlerts
from heshly_core.services.security.security_metrics import SecurityMetrics
from heshly_core.services.security.intrusion_detection import IntrusionDetection
from heshly_core.services.security.security_dashboard import SecurityDashboard
from heshly_core.services.security.alert_manager import AlertManager
from heshly_core.services.security.incident_reporting import IncidentReporting


class MockRepository:

    def __init__(self):
        self.items = []

    def save(self, item):
        self.items.append(item)
        return item

    def get(self, item_id):
        for item in self.items:
            if getattr(item, "id", None) == item_id:
                return item
        return None

    def list(self):
        return self.items

    def delete(self, item_id):
        self.items = [
            item
            for item in self.items
            if getattr(item, "id", None) != item_id
        ]

    def count(self):
        return len(self.items)       


def test_security_services():

    print("\n================================")
    print("Security Services Test")
    print("================================\n")

    audit_repository = AuditRepository()

    metrics = SecurityMetrics()
    alerts = SecurityAlerts()
    intrusion = IntrusionDetection()

    audit = AuditService(audit_repository)
    tracker = ActivityTracker(audit)
    compliance = ComplianceReporting(audit_repository)

    dashboard = SecurityDashboard(
        metrics,
        alerts,
        intrusion,
    )

    alert_manager = AlertManager(alerts)

    incident_reporting = IncidentReporting(
        metrics,
        intrusion,
        alert_manager,
    )

    encryption_service = EncryptionService(
        secret="test-encryption-secret",
    )

    secret_manager = SecretManager(
        encryption_service=encryption_service,
    )

    secure_configuration = SecureConfiguration(
        secret_manager=secret_manager,
    )

    authorization = AuthorizationManager(
        role_repository=MockRepository(),
        permission_repository=MockRepository(),
        assignment_repository=MockRepository(),
    )

    services = SecurityServices(

        authentication_manager=AuthenticationService(),

        authorization_manager=authorization,

        session_manager=SessionManager(),

        token_manager=TokenManager(),

        jwt_manager=JWTManager(
            secret="test-secret",
        ),

        refresh_token_manager=RefreshTokenManager(),

        token_revocation=TokenRevocation(),

        encryption_service=encryption_service,

        secret_manager=secret_manager,

        secure_configuration=secure_configuration,

        data_masking=DataMasking(),

        audit_service=audit,

        activity_tracker=tracker,

        compliance_reporting=compliance,

        brute_force_protection=BruteForceProtection(),

        account_lockout=AccountLockout(),

        suspicious_activity_detection=SuspiciousActivityDetection(),

        ip_allow_deny_lists=IPAccessControl(),

        security_alerts=alerts,

        security_metrics=metrics,

        intrusion_detection=intrusion,

        security_dashboard=dashboard,

        alert_manager=alert_manager,

        incident_reporting=incident_reporting,
    )

    print("✅ Container created")

    assert services.has("authentication_manager")
    assert services.has("authorization_manager")
    assert services.has("session_manager")
    assert services.has("token_manager")
    assert services.has("jwt_manager")
    assert services.has("refresh_token_manager")
    assert services.has("token_revocation")
    assert services.has("encryption_service")
    assert services.has("secret_manager")
    assert services.has("secure_configuration")
    assert services.has("audit_service")

    print("✅ Registry")

    health = services.health()

    assert "status" in health
    assert "services" in health

    print("✅ Health aggregation")

    print("\n🎉 SECURITY SERVICES TEST PASSED\n")
