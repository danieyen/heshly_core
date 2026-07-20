from heshly_core.services.auth.password_manager import (
    PasswordManager,
)


def run_test():

    print("\n================================")
    print("Password Manager Test")
    print("================================\n")


    manager = PasswordManager()


    password = "SecurePass123!"


    password_hash = manager.hash_password(
        password
    )


    assert password_hash != password

    print("✅ Password hashed")


    assert manager.verify_password(

        password,

        password_hash,

    )

    print("✅ Password verified")


    assert not manager.verify_password(

        "WrongPassword",

        password_hash,

    )

    print("✅ Invalid password rejected")


    valid, message = manager.validate_strength(
        password
    )

    assert valid

    print("✅ Strong password accepted")


    valid, message = manager.validate_strength(
        "abc"
    )

    assert not valid

    print("✅ Weak password rejected")


    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")


    print(
        "\n🎉 PASSWORD MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()