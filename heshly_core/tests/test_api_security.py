from heshly_core.models.api_key import (
    APIKeyScope,
)
from heshly_core.repositories.api_key_repository import (
    APIKeyRepository,
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


def run_test():

    print("\n================================")
    print("API Security Integration Test")
    print("================================\n")

    # =====================================================
    # Setup
    # =====================================================

    repository = APIKeyRepository()

    key_manager = APIKeyManager(
        repository
    )

    signature_validator = (
        RequestSignatureValidator()
    )

    webhook_verifier = (
        WebhookVerifier(
            repository,
            signature_validator,
        )
    )

    # =====================================================
    # Create API Key
    # =====================================================

    api_key, secret = key_manager.create_key(

        key_id="key001",

        tenant_id="tenant001",

        name="Production",

        scope=APIKeyScope.ADMIN,

        created_by="system",

        expires_in_days=30,

    )

    assert repository.count() == 1

    print("✅ API key created")

    # =====================================================
    # Validate API Key
    # =====================================================

    validated = key_manager.validate(
        secret
    )

    assert validated is not None

    print("✅ API key validated")

    # =====================================================
    # Generate Signature
    # =====================================================

    payload = """
    {
        "event":"appointment.created",
        "appointment":"APT001"
    }
    """.strip()

    signature = (
        signature_validator.generate(
            secret,
            payload,
        )
    )

    assert signature_validator.validate(

        secret,

        payload,

        signature,

    )

    print("✅ Signature validated")

    # =====================================================
    # Verify Webhook
    # =====================================================

    verified = webhook_verifier.verify(

        key_hash=api_key.key_hash,

        payload=payload,

        signature=signature,

        secret=secret,

    )

    assert verified is not None

    print("✅ Webhook verified")

    # =====================================================
    # Invalid Signature
    # =====================================================

    invalid = webhook_verifier.verify(

        key_hash=api_key.key_hash,

        payload=payload,

        signature="invalid",

        secret=secret,

    )

    assert invalid is None

    print("✅ Invalid signature rejected")

    # =====================================================
    # Disable Key
    # =====================================================

    assert key_manager.disable(
        api_key.key_id
    )

    assert key_manager.validate(
        secret
    ) is None

    print("✅ Disabled key rejected")

    # =====================================================
    # Enable Key
    # =====================================================

    assert key_manager.enable(
        api_key.key_id
    )

    assert key_manager.validate(
        secret
    ) is not None

    print("✅ Enabled key accepted")

    # =====================================================
    # Revoke Key
    # =====================================================

    assert key_manager.revoke(
        api_key.key_id
    )

    assert key_manager.validate(
        secret
    ) is None

    print("✅ Revoked key rejected")

    # =====================================================
    # Health Checks
    # =====================================================

    assert (
        key_manager.health()["status"]
        ==
        "healthy"
    )

    assert (
        signature_validator.health()["status"]
        ==
        "healthy"
    )

    assert (
        webhook_verifier.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health checks")

    print("\n🎉 API SECURITY TEST PASSED\n")


if __name__ == "__main__":

    run_test()