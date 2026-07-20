from heshly_core.services.integration.security_health_check import (
    SecurityHealthCheck,
)



class FakeService:

    def health(self):

        return {

            "status":
                "healthy"

        }



def run_test():

    print("\n================================")
    print("Security Health Check Test")
    print("================================\n")


    checker = SecurityHealthCheck(

        authentication_integration=FakeService(),

        authorization_integration=FakeService(),

        encryption_integration=FakeService(),

        audit_integration=FakeService(),

        security_metrics=FakeService(),

        security_dashboard=FakeService(),

    )


    print("✅ Health checker initialized")


    result = checker.check()


    assert (
        result["status"]
        ==
        "healthy"
    )


    print("✅ Full security health")


    assert checker.is_healthy()


    print("✅ Health status")


    assert (
        checker.health()["status"]
        ==
        "healthy"
    )


    print("✅ Service health")


    print(
        "\n🎉 SECURITY HEALTH CHECK TEST PASSED\n"
    )



if __name__ == "__main__":

    run_test()