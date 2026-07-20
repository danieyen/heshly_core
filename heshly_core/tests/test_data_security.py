from heshly_core.services.security.data_masking import (
    DataMasking,
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
from heshly_core.services.security.sensitive_data_protection import (
    SensitiveDataProtection,
)


def run_test():

    print("\n================================")
    print("Data Security Integration Test")
    print("================================\n")

    # =====================================================
    # Setup
    # =====================================================

    encryption = EncryptionService(
        "heshly-master-key"
    )

    masking = DataMasking()

    secret_manager = SecretManager(
        encryption
    )

    configuration = SecureConfiguration(
        secret_manager
    )

    protection = SensitiveDataProtection(

        encryption,

        masking,

    )

    print("✅ Services initialized")

    # =====================================================
    # Encryption
    # =====================================================

    plaintext = "Highly Confidential Data"

    encrypted = protection.encrypt(
        plaintext
    )

    assert encrypted != plaintext

    decrypted = protection.decrypt(
        encrypted
    )

    assert decrypted == plaintext

    print("✅ Encryption / Decryption")

    # =====================================================
    # Hashing
    # =====================================================

    digest = protection.hash(
        plaintext
    )

    assert protection.verify_hash(

        plaintext,

        digest,

    )

    print("✅ Hash verification")

    # =====================================================
    # Secret Manager
    # =====================================================

    secret_manager.set_secret(

        "openai",

        "sk-secret-key",

    )

    assert secret_manager.exists(
        "openai"
    )

    assert (

        secret_manager.get_secret(
            "openai"
        )

        ==

        "sk-secret-key"

    )

    print("✅ Secret storage")

    rotated = secret_manager.rotate_secret(
        "openai"
    )

    assert (

        secret_manager.get_secret(
            "openai"
        )

        ==

        rotated

    )

    print("✅ Secret rotation")

    # =====================================================
    # Secure Configuration
    # =====================================================

    configuration.set(

        "timezone",

        "Africa/Nairobi",

    )

    configuration.set(

        "currency",

        "KES",

    )

    configuration.set_secret(

        "database",

        "mysql-password",

    )

    assert (

        configuration.get(
            "timezone"
        )

        ==

        "Africa/Nairobi"

    )

    assert (

        configuration.get_secret(
            "database"
        )

        ==

        "mysql-password"

    )

    exported = configuration.export()

    assert "database" not in exported

    print("✅ Secure configuration")

    # =====================================================
    # Data Masking
    # =====================================================

    assert (

        protection.mask_email(
            "daniel@example.com"
        )

        ==

        "da****@example.com"

    )

    masked_phone = protection.mask_phone(
        "+254712345678"
    )

    assert masked_phone.endswith(
        "5678"
    )

    masked_key = protection.mask_api_key(
        "abcdefghijklmnopqrstuvwxyz"
    )

    assert masked_key.startswith(
        "abcd"
    )

    print("✅ Individual masking")

    payload = {

        "username": "admin",

        "password": "secret123",

        "token": "abcdef",

        "api_key": "xyz987",

        "tenant": "tenant001",

    }

    sanitized = protection.sanitize(
        payload
    )

    assert sanitized["username"] == "admin"

    assert sanitized["tenant"] == "tenant001"

    assert sanitized["password"] == "*********"

    assert sanitized["token"] == "******"

    assert sanitized["api_key"] == "******"

    print("✅ Payload sanitization")

    # =====================================================
    # Cleanup
    # =====================================================

    assert secret_manager.delete_secret(
        "openai"
    )

    assert configuration.delete(
        "currency"
    )

    assert configuration.delete_secret(
        "database"
    )

    print("✅ Cleanup")

    # =====================================================
    # Health Checks
    # =====================================================

    assert (

        encryption.health()["status"]

        ==

        "healthy"

    )

    assert (

        masking.health()["status"]

        ==

        "healthy"

    )

    assert (

        secret_manager.health()["status"]

        ==

        "healthy"

    )

    assert (

        configuration.health()["status"]

        ==

        "healthy"

    )

    assert (

        protection.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health checks")

    print("\n🎉 DATA SECURITY TEST PASSED\n")


if __name__ == "__main__":

    run_test()