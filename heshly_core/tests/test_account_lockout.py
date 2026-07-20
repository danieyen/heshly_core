from heshly_core.services.security.account_lockout import (
    AccountLockout,
)


def run_test():

    print("\n================================")
    print("Account Lockout Test")
    print("================================\n")

    manager = AccountLockout()

    user = "user001"

    manager.lock(
        user
    )

    assert manager.is_locked(
        user
    )

    print("✅ Account locked")

    assert manager.get(
        user
    ) is not None

    print("✅ Lock retrieved")

    assert (

        manager.remaining_lock_time(
            user
        )

        >

        0

    )

    print("✅ Remaining lock time")

    manager.unlock(
        user
    )

    assert not manager.is_locked(
        user
    )

    print("✅ Account unlocked")

    assert manager.count() == 0

    print("✅ Repository empty")

    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 ACCOUNT LOCKOUT TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()