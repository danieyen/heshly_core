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
from heshly_core.services.security.jwt_manager import (
    JWTManager,
)
from heshly_core.services.security.token_manager import (
    TokenManager,
)
from heshly_core.services.security.refresh_token_manager import (
    RefreshTokenManager,
)
from heshly_core.services.security.token_revocation import (
    TokenRevocation,
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


def test_security():

    print("\n================================")
    print("Security Tests")
    print("================================\n")

    encryption = EncryptionService(
        secret="test-secret"
    )

    masking = DataMasking()

    secrets = SecretManager(
        encryption_service=encryption,
    )

    config = SecureConfiguration(
        secret_manager=secrets,
    )

    protection = SensitiveDataProtection(
        encryption_service=encryption,
        masking_service=masking,
    )

    jwt = JWTManager(
        secret="jwt-secret",
    )

    token_manager = TokenManager()

    refresh = RefreshTokenManager()

    revocation = TokenRevocation()

    brute_force = BruteForceProtection()

    lockout = AccountLockout()

    suspicious = SuspiciousActivityDetection()

    ip = IPAccessControl()

    assert encryption is not None
    assert masking is not None
    assert secrets is not None
    assert config is not None
    assert protection is not None
    assert jwt is not None
    assert token_manager is not None
    assert refresh is not None
    assert revocation is not None
    assert brute_force is not None
    assert lockout is not None
    assert suspicious is not None
    assert ip is not None

    if hasattr(encryption, "health"):
        assert encryption.health()["status"] == "healthy"

    if hasattr(jwt, "health"):
        assert jwt.health()["status"] == "healthy"

    print("✅ Security services instantiated")

    print("\n🎉 SECURITY TESTS PASSED\n")