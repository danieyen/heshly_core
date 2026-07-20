import os

from heshly_core.config.environment import Environment


def test_environment_variables():

    print("\n================================")
    print("Environment Variables")
    print("================================\n")

    os.environ["HESHLY_ENV"] = "production"

    os.environ["JWT_SECRET"] = "secret"

    os.environ["DATABASE_URL"] = "mysql://localhost"

    assert Environment.is_production()

    assert (
        Environment.get("JWT_SECRET")
        == "secret"
    )

    assert (
        Environment.required("DATABASE_URL")
        == "mysql://localhost"
    )

    print("Environment :", Environment.get("HESHLY_ENV"))

    print("JWT Secret  :", Environment.get("JWT_SECRET"))

    print("Database    :", Environment.get("DATABASE_URL"))

    print("\n🎉 ENVIRONMENT VARIABLES PASSED\n")