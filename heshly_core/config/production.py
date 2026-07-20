from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class ProductionConfig:
    """
    Production environment configuration.
    """

    app_name: str = os.getenv(
        "HESHLY_APP_NAME",
        "Heshly",
    )

    environment: str = os.getenv(
        "HESHLY_ENV",
        "production",
    )

    debug: bool = False

    secret_key: str = os.getenv(
        "HESHLY_SECRET_KEY",
        "CHANGE_ME",
    )

    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql://localhost/heshly",
    )

    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )

    api_host: str = os.getenv(
        "API_HOST",
        "0.0.0.0",
    )

    api_port: int = int(
        os.getenv(
            "API_PORT",
            "8000",
        )
    )

    workers: int = int(
        os.getenv(
            "WORKERS",
            "4",
        )
    )

    log_level: str = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )

    timezone: str = os.getenv(
        "TIMEZONE",
        "Africa/Nairobi",
    )

    ssl_enabled: bool = True

    cors_enabled: bool = False

    rate_limit_per_minute: int = 300

    jwt_expiry_minutes: int = 60

    backup_enabled: bool = True

    monitoring_enabled: bool = True

    metrics_enabled: bool = True


config = ProductionConfig()