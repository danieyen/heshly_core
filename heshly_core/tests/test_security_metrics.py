from heshly_core.services.security.security_metrics import (
    SecurityMetrics,
)


def run_test():

    print("\n================================")
    print("Security Metrics Test")
    print("================================\n")

    metrics = SecurityMetrics()

    metrics.register(

        "failed_logins",

        "Failed login attempts",

    )

    metrics.increment(
        "failed_logins"
    )

    metrics.increment(
        "failed_logins",
        4,
    )

    assert (

        metrics.value(
            "failed_logins"
        )

        ==

        5

    )

    print("✅ Increment")

    metrics.decrement(
        "failed_logins",
        2,
    )

    assert (

        metrics.value(
            "failed_logins"
        )

        ==

        3

    )

    print("✅ Decrement")

    metrics.set(

        "blocked_ips",

        12,

    )

    assert (

        metrics.value(
            "blocked_ips"
        )

        ==

        12

    )

    print("✅ Set value")

    snapshot = metrics.snapshot()

    assert snapshot["failed_logins"] == 3

    assert snapshot["blocked_ips"] == 12

    print("✅ Snapshot")

    assert (

        metrics.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 SECURITY METRICS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()