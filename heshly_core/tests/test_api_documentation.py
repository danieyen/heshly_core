from heshly_core.services.api.api_documentation import (
    APIDocumentationService,
)


def run_test():

    print("\n================================")
    print("API Documentation Test")
    print("================================\n")


    docs = APIDocumentationService()


    docs.register_endpoint(

        "/api/v1/tenants",

        "GET",

        "List tenants",

        [

            "tenant.view"

        ]

    )


    print(
        "✅ Endpoint registered"
    )


    documentation = (
        docs.get_documentation()
    )


    assert (
        documentation.version
        ==
        "v1"
    )


    print(
        "✅ API version available"
    )


    assert len(
        docs.endpoints()
    ) == 1


    print(
        "✅ Endpoint listing works"
    )


    endpoint = (
        docs.endpoints()[0]
    )


    assert (
        endpoint.path
        ==
        "/api/v1/tenants"
    )


    print(
        "✅ Endpoint schema validated"
    )


    assert (
        docs.health()["status"]
        ==
        "healthy"
    )


    print(
        "✅ Health check"
    )


    print(
        "\n🎉 API DOCUMENTATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()