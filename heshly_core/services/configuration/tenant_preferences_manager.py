from __future__ import annotations

from heshly_core.models.tenant_preferences import (
    TenantPreferences,
)

from heshly_core.repositories.tenant_preferences_repository import (
    TenantPreferencesRepository,
)


class TenantPreferencesManager:

    """
    Tenant Preferences Manager.
    """

    def __init__(self):

        self.repository = (
            TenantPreferencesRepository()
        )

    def create(
        self,
        tenant_id: str,
    ) -> TenantPreferences:

        preferences = TenantPreferences(
            tenant_id=tenant_id
        )

        self.repository.save(
            preferences
        )

        return preferences

    def get(
        self,
        tenant_id: str,
    ) -> TenantPreferences | None:

        return self.repository.get(
            tenant_id
        )

    def get_or_create(
        self,
        tenant_id: str,
    ) -> TenantPreferences:

        preferences = self.get(
            tenant_id
        )

        if preferences is None:

            preferences = self.create(
                tenant_id
            )

        return preferences

    def update(
        self,
        tenant_id: str,
        **kwargs,
    ) -> TenantPreferences:

        preferences = self.get_or_create(
            tenant_id
        )

        preferences.update(
            **kwargs
        )

        self.repository.save(
            preferences
        )

        return preferences

    def health(self):

        return {

            "service": "tenant_preferences_manager",

            "status": "healthy",

        }