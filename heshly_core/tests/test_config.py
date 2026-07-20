"""
Heshly Test Configuration

Central configuration shared across
unit, integration and e2e tests.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


TEST_ENVIRONMENT = "test"


DEFAULT_TENANT_ID = "tenant001"

DEFAULT_USER_ID = "user001"


class TestConfig:
    """
    Global test configuration.
    """

    environment = TEST_ENVIRONMENT

    project_root = PROJECT_ROOT

    tenant_id = DEFAULT_TENANT_ID

    user_id = DEFAULT_USER_ID
