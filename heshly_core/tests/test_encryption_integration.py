from heshly_core.services.integration.encryption_integration import (
    EncryptionIntegration,
)



class FakeEncryptionService:

    def encrypt(
        self,
        data,
    ):

        return f"encrypted:{data}"


    def decrypt(
        self,
        data,
    ):

        return data.replace(
            "encrypted:",
            "",
        )



class FakeSecretManager:

    def __init__(self):

        self.data = {}


    def set(
        self,
        key,
        value,
    ):

        self.data[key] = value

        return True


    def get(
        self,
        key,
    ):

        return self.data.get(
            key
        )



class FakeConfiguration:

    def get(
        self,
        key,
    ):

        return "value"



class FakeMasking:

    def mask(
        self,
        data,
    ):

        return "***"



class FakeProtection:

    def protect(
        self,
        data,
    ):

        return {
            "protected": data
        }



class FakeAudit:
    pass



class FakeMetrics:

    def increment(
        self,
        name,
    ):

        pass



def run_test():

    print("\n================================")
    print("Encryption Integration Test")
    print("================================\n")


    integration = EncryptionIntegration(

        encryption_service=FakeEncryptionService(),

        secret_manager=FakeSecretManager(),

        secure_configuration=FakeConfiguration(),

        data_masking=FakeMasking(),

        sensitive_data_protection=FakeProtection(),

        audit_service=FakeAudit(),

        security_metrics=FakeMetrics(),

    )


    print("✅ Services initialized")


    encrypted = integration.encrypt(
        "secret",
    )

    assert encrypted.data == "encrypted:secret"

    print("✅ Encryption")


    decrypted = integration.decrypt(
        "encrypted:secret",
    )

    assert decrypted.data == "secret"

    print("✅ Decryption")


    integration.store_secret(
        "api_key",
        "123",
    )


    assert integration.get_secret(
        "api_key"
    ) == "123"


    print("✅ Secret management")


    assert integration.get_configuration(
        "mode"
    ) == "value"


    print("✅ Secure configuration")


    assert integration.mask(
        "123456"
    ) == "***"


    print("✅ Data masking")


    assert integration.protect_sensitive_data(
        "private"
    )["protected"] == "private"


    print("✅ Sensitive protection")


    assert (
        integration.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health")


    print(
        "\n🎉 ENCRYPTION INTEGRATION TEST PASSED\n"
    )



if __name__ == "__main__":

    run_test()