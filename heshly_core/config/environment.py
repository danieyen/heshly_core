from __future__ import annotations

import os


class Environment:

    @staticmethod
    def get(
        key: str,
        default=None,
    ):

        return os.getenv(
            key,
            default,
        )

    @staticmethod
    def required(
        key: str,
    ):

        value = os.getenv(key)

        if value is None:

            raise RuntimeError(
                f"Missing environment variable: {key}"
            )

        return value

    @staticmethod
    def is_production():

        return (
            os.getenv(
                "HESHLY_ENV",
                "development",
            )
            == "production"
        )