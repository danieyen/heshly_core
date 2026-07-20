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
    print("Webhook Verifier Test")
    print("================================\n")

    repository = APIKeyRepository()

    key_manager = APIKeyManager(
        repository
    )

    validator = RequestSignatureValidator()

    verifier = WebhookVerifier(

        repository,

        validator,

    )

    api_key, secret = key_manager.create_key(

        key_id="key001",

        tenant_id="tenant001",

        name="Webhook",

    )

    payload = """

    {

        "event":"appointment.created",

        "appointment":"APT001"

    }

    """.strip()

    signature = validator.generate(

        secret,

        payload,

    )

    verified = verifier.verify(

        key_hash=api_key.key_hash,

        payload=payload,

        signature=signature,

        secret=secret,

    )

    assert verified is not None

    print("✅ Valid webhook accepted")

    invalid = verifier.verify(

        key_hash=api_key.key_hash,

        payload=payload,

        signature="invalid",

        secret=secret,

    )

    assert invalid is None

    print("✅ Invalid signature rejected")

    invalid = verifier.verify(

        key_hash="unknown",

        payload=payload,

        signature=signature,

        secret=secret,

    )

    assert invalid is None

    print("✅ Unknown API key rejected")

    key_manager.disable(
        api_key.key_id
    )

    invalid = verifier.verify(

        key_hash=api_key.key_hash,

        payload=payload,

        signature=signature,

        secret=secret,

    )

    assert invalid is None

    print("✅ Disabled key rejected")

    assert (

        verifier.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print("\n🎉 WEBHOOK VERIFIER TEST PASSED\n")


if __name__ == "__main__":

    run_test()