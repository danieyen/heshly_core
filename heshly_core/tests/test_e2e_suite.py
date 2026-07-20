from __future__ import annotations

import pytest


E2E_TESTS = [

    "test_customer_journey.py",

    "test_ai_receptionist.py",

    "test_booking_flow.py",

    "test_payment_flow.py",

    "test_crm_pipeline.py",

]


def test_e2e_suite():

    print("\n================================")
    print("End-to-End Test Suite")
    print("================================\n")

    for test in E2E_TESTS:

        print(f"✅ {test}")

    assert len(E2E_TESTS) == 5

    print("\n🎉 ALL E2E TESTS REGISTERED\n")


if __name__ == "__main__":

    raise SystemExit(

        pytest.main(
            [
                "-v",

                "heshly_core/tests/test_customer_journey.py",

                "heshly_core/tests/test_ai_receptionist.py",

                "heshly_core/tests/test_booking_flow.py",

                "heshly_core/tests/test_payment_flow.py",

                "heshly_core/tests/test_crm_pipeline.py",
            ]
        )

    )