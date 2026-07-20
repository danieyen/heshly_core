from __future__ import annotations

from heshly_core.services.integration.service_container import (
    ServiceContainer,
)

# =====================================================
# Authentication
# =====================================================

from heshly_core.services.auth.authentication_service import (
    AuthenticationService,
)
from heshly_core.services.auth.authorization_manager import (
    AuthorizationManager,
)
from heshly_core.services.auth.login_manager import (
    LoginManager,
)
from heshly_core.services.auth.password_manager import (
    PasswordManager,
)
from heshly_core.services.auth.session_manager import (
    SessionManager,
)

# =====================================================
# Security
# =====================================================

from heshly_core.services.security.token_manager import (
    TokenManager,
)
from heshly_core.services.security.jwt_manager import (
    JWTManager,
)
from heshly_core.services.security.refresh_token_manager import (
    RefreshTokenManager,
)
from heshly_core.services.security.token_revocation import (
    TokenRevocation,
)

from heshly_core.services.security.permission_manager import (
    PermissionManager,
)

from heshly_core.services.security.api_key_manager import (
    APIKeyManager,
)

from heshly_core.services.security.request_signature_validator import (
    RequestSignatureValidator,
)

from heshly_core.services.security.webhook_verifier import (
    WebhookVerifier,
)

from heshly_core.services.security.encryption_service import (
    EncryptionService,
)

from heshly_core.services.security.secret_manager import (
    SecretManager,
)

from heshly_core.services.security.secure_configuration import (
    SecureConfiguration,
)

from heshly_core.services.security.data_masking import (
    DataMasking,
)

from heshly_core.services.security.sensitive_data_protection import (
    SensitiveDataProtection,
)

from heshly_core.services.security.audit_service import (
    AuditService,
)

from heshly_core.services.security.activity_tracker import (
    ActivityTracker,
)

from heshly_core.services.security.compliance_reporting import (
    ComplianceReporting,
)

from heshly_core.services.security.brute_force_protection import (
    BruteForceProtection,
)

from heshly_core.services.security.account_lockout import (
    AccountLockout,
)

from heshly_core.services.security.suspicious_activity_detection import (
    SuspiciousActivityDetection,
)

from heshly_core.services.security.ip_access_control import (
    IPAccessControl,
)

from heshly_core.services.security.security_alerts import (
    SecurityAlerts,
)

from heshly_core.services.security.security_metrics import (
    SecurityMetrics,
)

from heshly_core.services.security.intrusion_detection import (
    IntrusionDetection,
)

from heshly_core.services.security.security_dashboard import (
    SecurityDashboard,
)

from heshly_core.services.security.alert_manager import (
    AlertManager,
)

from heshly_core.services.security.incident_reporting import (
    IncidentReporting,
)


class SecurityServices(ServiceContainer):

    """
    Root dependency container for the
    complete Heshly security subsystem.

    This class contains no business logic.
    """

    pass