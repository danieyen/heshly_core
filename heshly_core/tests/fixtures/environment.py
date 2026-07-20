import os
from pathlib import Path


ENV_FILE = Path(__file__).parent.parent / ".env.test"


def load_test_environment():

    if not ENV_FILE.exists():
        return


    with open(ENV_FILE) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            key, value = line.split(
                "=",
                1
            )

            os.environ.setdefault(
                key,
                value
            )


def get_test_environment():

    load_test_environment()

    return {

        "environment": os.getenv(
            "ENVIRONMENT"
        ),

        "tenant_id": os.getenv(
            "TENANT_ID"
        ),

        "user_id": os.getenv(
            "USER_ID"
        ),

        "database": os.getenv(
            "DATABASE_NAME"
        ),

    }
