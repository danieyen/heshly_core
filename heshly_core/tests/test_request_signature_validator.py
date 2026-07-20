from heshly_core.services.security.request_signature_validator import (
    RequestSignatureValidator,
)


def run_test():

    print("\n================================")
    print("Request Signature Validation Test")
    print("================================\n")

    validator = RequestSignatureValidator()

    secret = "my-secret"

    payload = '{"tenant":"tenant001","message":"hello"}'

    signature = validator.generate(

        secret,

        payload,

    )

    print("✅ Signature generated")

    assert validator.validate(

        secret,

        payload,

        signature,

    )

    print("✅ Valid signature accepted")

    assert not validator.validate(

        secret,

        payload,

        "invalid-signature",

    )

    print("✅ Invalid signature rejected")

    altered_payload = '{"tenant":"tenant001","message":"bye"}'

    assert not validator.validate(

        secret,

        altered_payload,

        signature,

    )

    print("✅ Modified payload rejected")

    assert (

        validator.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print("\n🎉 REQUEST SIGNATURE VALIDATION TEST PASSED\n")


if __name__ == "__main__":

    run_test()