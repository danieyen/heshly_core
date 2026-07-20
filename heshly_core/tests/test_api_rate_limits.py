from heshly_core.services.auth.api_rate_limits import (
    APIRateLimits,
)


def run_test():

    print("\n================================")
    print("API Rate Limits Test")
    print("================================\n")


    limiter = APIRateLimits()


    limiter.set_rule(

        "tenant001",

        requests=3,

        window_seconds=60,

    )


    print("✅ Rate rule created")


    assert limiter.allow(
        "tenant001"
    )

    assert limiter.allow(
        "tenant001"
    )

    assert limiter.allow(
        "tenant001"
    )


    print("✅ Requests allowed")


    blocked = limiter.allow(
        "tenant001"
    )


    assert blocked is False


    print(
        "✅ Excess requests blocked"
    )


    try:

        limiter.require(
            "tenant001"
        )

        assert False


    except PermissionError:

        print(
            "✅ Limit exception raised"
        )


    assert (

        limiter.health()["status"]

        ==

        "healthy"

    )


    print(
        "✅ Health check"
    )


    print(
        "\n🎉 API RATE LIMITS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()