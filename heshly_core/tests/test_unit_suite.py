from __future__ import annotations

import pytest


UNIT_TESTS = [
    "heshly_core/tests/test_models.py",
    "heshly_core/tests/test_services.py",
    "heshly_core/tests/test_repositories.py",
    "heshly_core/tests/test_utilities.py",
    "heshly_core/tests/test_security_services.py",
]


def test_unit_suite_exists():
    """
    Verify all expected unit test files exist.
    """

    import os

    missing = [
        path
        for path in UNIT_TESTS
        if not os.path.exists(path)
    ]

    assert missing == []


def test_pytest_available():
    """
    Ensure pytest is installed.
    """

    assert pytest.__version__ is not None


def test_unit_suite_definition():
    """
    Verify suite configuration.
    """

    assert len(UNIT_TESTS) == 5