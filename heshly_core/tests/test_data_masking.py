from heshly_core.services.security.data_masking import (
    DataMasking,
)


def run_test():

    print("\n================================")
    print("Data Masking Test")
    print("================================\n")

    masking = DataMasking()

    email = masking.mask_email(
        "daniel@example.com"
    )

    assert email == "da****@example.com"

    print("✅ Email masking")

    phone = masking.mask_phone(
        "+254712345678"
    )

    assert phone.endswith(
        "5678"
    )

    print("✅ Phone masking")

    api_key = masking.mask_api_key(
        "abcdefghijklmnopqrstuvwxyz"
    )

    assert api_key.startswith(
        "abcd"
    )

    assert api_key.endswith(
        "wxyz"
    )

    print("✅ API key masking")

    secret = masking.mask_secret(
        "my-secret"
    )

    assert secret == "*********"

    print("✅ Secret masking")

    payload = {

        "username": "admin",

        "password": "secret123",

        "token": "abcdef",

        "api_key": "xyz987",

    }

    masked = masking.mask_dictionary(
        payload
    )

    assert masked["username"] == "admin"

    assert masked["password"] == "*********"

    assert masked["token"] == "******"

    assert masked["api_key"] == "******"

    print("✅ Dictionary masking")

    assert (

        masking.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 DATA MASKING TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()