from heshly_core.services.integration.authorization_integration import (
    AuthorizationIntegration,
)


class FakeAuthorizationManager:

    def has_permission(
        self,
        user,
        resource,
        action,
    ):

        return (
            resource == "crm"
            and action == "read"
        )



class FakePermissionManager:
    pass



class FakeAPIKeyManager:

    def validate(
        self,
        key,
    ):

        return key == "valid"



class FakeSignatureValidator:

    def validate(
        self,
        payload,
        signature,
        secret,
    ):

        return True



class FakeWebhookVerifier:

    def verify(
        self,
        payload,
        signature,
    ):

        return True



class FakeAudit:

    def access_denied(
        self,
        **kwargs,
    ):

        pass



class FakeMetrics:

    def increment(
        self,
        name,
    ):

        pass



class User:

    user_id = "user001"

    tenant_id = "tenant001"



def run_test():

    print("\n================================")
    print("Authorization Integration Test")
    print("================================\n")


    integration = AuthorizationIntegration(

        authorization_manager=FakeAuthorizationManager(),

        permission_manager=FakePermissionManager(),

        api_key_manager=FakeAPIKeyManager(),

        request_signature_validator=FakeSignatureValidator(),

        webhook_verifier=FakeWebhookVerifier(),

        audit_service=FakeAudit(),

        security_metrics=FakeMetrics(),

    )


    print("✅ Services initialized")


    result = integration.authorize(

        User(),

        "crm",

        "read",

    )


    assert result.allowed

    print("✅ Permission granted")


    denied = integration.authorize(

        User(),

        "crm",

        "delete",

    )


    assert not denied.allowed

    print("✅ Permission denied")


    assert integration.validate_api_key(
        "valid"
    )


    print("✅ API key validation")


    assert integration.validate_signature(
        "payload",
        "signature",
        "secret",
    )


    print("✅ Signature validation")


    assert integration.verify_webhook(
        "payload",
        "signature",
    )


    print("✅ Webhook verification")


    assert (
        integration.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health")


    print(
        "\n🎉 AUTHORIZATION INTEGRATION TEST PASSED\n"
    )



if __name__ == "__main__":

    run_test()