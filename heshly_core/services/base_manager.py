from __future__ import annotations

from datetime import UTC, datetime


class BaseManager:
    """
    Base class for all Heshly managers.

    Provides common functionality shared by
    every service manager.
    """

    SERVICE_NAME = "base_manager"

    VERSION = "1.0.0"

    def __init__(self):

        self.started_at = datetime.now(
            UTC
        )

    # =====================================================
    # Information
    # =====================================================

    @property
    def service_name(self) -> str:

        return self.SERVICE_NAME

    @property
    def version(self) -> str:

        return self.VERSION

    # =====================================================
    # Status
    # =====================================================

    def status(self) -> str:

        return "healthy"

    def ping(self) -> bool:

        return True

    # =====================================================
    # Lifecycle
    # =====================================================

    def startup(self):

        """
        Reserved for future startup logic.
        """

        return True

    def shutdown(self):

        """
        Reserved for future shutdown logic.
        """

        return True

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "service": self.service_name,

            "status": self.status(),

            "version": self.version,

            "started_at": self.started_at,

        }