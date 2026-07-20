from heshly_core.services.security.brute_force_protection import (
    BruteForceProtection,
)


def run_test():

    print("\n================================")
    print("Brute Force Protection Test")
    print("================================\n")

    protection = BruteForceProtection()

    username = "admin@example.com"

    ip = "192.168.1.10"

    for i in range(4):

        protection.record_failure(
            username,
            ip,
        )

    assert not protection.is_blocked(
        username,
        ip,
    )

    print("✅ Not blocked after four failures")

    protection.record_failure(
        username,
        ip,
    )

    assert protection.is_blocked(
        username,
        ip,
    )

    print("✅ Blocked after fifth failure")

    assert (
        protection.remaining_attempts(
            username,
            ip,
        )
        == 0
    )

    print("✅ Remaining attempts")

    protection.unlock(
        username,
        ip,
    )

    assert not protection.is_blocked(
        username,
        ip,
    )

    print("✅ Unlock successful")

    assert protection.count() == 0

    print("✅ Repository cleared")

    assert (
        protection.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check")

    print(
        "\n🎉 BRUTE FORCE PROTECTION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()