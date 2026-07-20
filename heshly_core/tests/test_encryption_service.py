from heshly_core.services.security.encryption_service import (
    EncryptionService,
)


def run_test():

    print("\n================================")
    print("Encryption Service Test")
    print("================================\n")

    service = EncryptionService(
        "my-secret-key"
    )

    plaintext = (
        "Sensitive customer data"
    )

    encrypted = service.encrypt(
        plaintext
    )

    assert encrypted != plaintext

    print("✅ Encryption successful")

    decrypted = service.decrypt(
        encrypted
    )

    assert decrypted == plaintext

    print("✅ Decryption successful")

    digest = service.hash(
        plaintext
    )

    assert service.verify_hash(

        plaintext,

        digest,

    )

    print("✅ Hash verification")

    secret = service.generate_secret()

    assert isinstance(
        secret,
        str,
    )

    assert len(secret) > 20

    print("✅ Secret generation")

    assert (

        service.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 ENCRYPTION SERVICE TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()