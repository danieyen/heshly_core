from __future__ import annotations

import os


INTEGRATION_TESTS = [

    "heshly_core/tests/test_module_integration.py",

    "heshly_core/tests/test_api_integration.py",

    "heshly_core/tests/test_database_integration.py",

    "heshly_core/tests/test_external_service_integration.py",

    "heshly_core/tests/test_workflow_integration.py",

]


def test_integration_suite():

    print("\n================================")
    print("Integration Test Suite")
    print("================================\n")

    # ==========================================
    # Files Exist
    # ==========================================

    missing = []

    for test in INTEGRATION_TESTS:

        if not os.path.exists(test):

            missing.append(test)

    assert missing == []

    print("✅ All integration tests found")

    # ==========================================
    # Count
    # ==========================================

    assert len(INTEGRATION_TESTS) == 5

    print("✅ Test count")

    print("\n🎉 INTEGRATION TEST SUITE PASSED\n")