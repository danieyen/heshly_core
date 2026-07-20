from heshly_core.services.security.data_masking import (
    DataMasking,
)
from heshly_core.services.security.encryption_service import (
    EncryptionService,
)
from heshly_core.services.security.sensitive_data_protection import (
    SensitiveDataProtection,
)


def run_test():

    print("\n================================")
    print("Sensitive Data Protection Test")
    print("================================\n")

    encryption = EncryptionService(
        "master-secret"
    )

    masking = DataMasking()

    protection = SensitiveDataProtection(

        encryption,

        masking,

    )

    # =====================================================
    # Encryption
    # =====================================================

    encrypted = protection.encrypt(
        "customer-data"
    )

    assert encrypted != "customer-data"

    decrypted = protection.decrypt(
        encrypted
    )

    assert decrypted == "customer-data"

    print("✅ Encryption & decryption")

    # =====================================================
    # Hashing
    # =====================================================

    digest = protection.hash(
        "password123"
    )

    assert protection.verify_hash(

        "password123",

        digest,

    )

    print("✅ Hash verification")

    # =====================================================
    # Email
    # =====================================================

    assert (

        protection.mask_email(
            "daniel@example.com"
        )

        ==

        "da****@example.com"

    )

    print("✅ Email masking")

    # =====================================================
    # Phone
    # =====================================================

    masked_phone = protection.mask_phone(
        "+254712345678"
    )

    assert masked_phone.endswith(
        "5678"
    )

    print("✅ Phone masking")

    # =====================================================
    # API Key
    # =====================================================

    masked_key = protection.mask_api_key(
        "abcdefghijklmnopqrstuvwxyz"
    )

    assert masked_key.startswith(
        "abcd"
    )

    print("✅ API key masking")

    # =====================================================
    # Dictionary
    # =====================================================

    payload = {

        "username": "admin",

        "password": "secret",

        "token": "abcdef",

    }

    sanitized = protection.sanitize(
        payload
    )

    assert sanitized["username"] == "admin"

    assert sanitized["password"] == "******"

    assert sanitized["token"] == "******"

    print("✅ Payload sanitization")

    # =====================================================
    # Health
    # =====================================================

    assert (

        protection.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 SENSITIVE DATA PROTECTION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()