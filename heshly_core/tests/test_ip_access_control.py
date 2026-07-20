from heshly_core.services.security.ip_access_control import (
    IPAccessControl,
)


def run_test():

    print("\n================================")
    print("IP Access Control Test")
    print("================================\n")

    control = IPAccessControl()

    assert control.is_allowed(
        "10.0.0.1"
    )

    print("✅ Default allow")

    control.deny_ip(

        "192.168.1.10",

        "Blocked attacker",

    )

    assert control.is_denied(
        "192.168.1.10"
    )

    assert not control.is_allowed(
        "192.168.1.10"
    )

    print("✅ Deny list")

    control.allow_ip(

        "10.10.10.10",

        "Office",

    )

    assert control.is_allowed(
        "10.10.10.10"
    )

    print("✅ Allow list")

    assert not control.is_allowed(
        "8.8.8.8"
    )

    print("✅ Allow list enforcement")

    control.remove_allowed_ip(
        "10.10.10.10"
    )

    control.remove_denied_ip(
        "192.168.1.10"
    )

    assert control.is_allowed(
        "8.8.8.8"
    )

    print("✅ Removal")

    health = control.health()

    assert health["status"] == "healthy"

    print("✅ Health check")

    print(
        "\n🎉 IP ACCESS CONTROL TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()