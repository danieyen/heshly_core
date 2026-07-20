from __future__ import annotations

import os


class SecretsManager:
    """
    Central secrets manager.

    Loads secrets from environment variables.
    """

    def get(
        self,
        name: str,
        default: str | None = None,
    ) -> str | None:

        return os.getenv(
            name,
            default,
        )

    def require(
        self,
        name: str,
    ) -> str:

        value = os.getenv(name)

        if not value:

            raise RuntimeError(
                f"Missing required secret: {name}"
            )

        return value

    def exists(
        self,
        name: str,
    ) -> bool:

        return os.getenv(name) is not None

    def all(
        self,
    ) -> dict[str, str]:

        return dict(os.environ)