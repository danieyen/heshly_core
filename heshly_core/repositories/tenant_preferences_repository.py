from __future__ import annotations

from heshly_core.models.tenant_preferences import (
    TenantPreferences,
)


class TenantPreferencesRepository:

    def __init__(self):

        self._preferences: dict[
            str,
            TenantPreferences,
        ] = {}

    def save(
        self,
        preferences: TenantPreferences,
    ) -> TenantPreferences:

        self._preferences[
            preferences.tenant_id
        ] = preferences

        return preferences

    def get(
        self,
        tenant_id: str,
    ) -> TenantPreferences | None:

        return self._preferences.get(
            tenant_id
        )

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return tenant_id in self._preferences

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        if tenant_id not in self._preferences:

            return False

        del self._preferences[
            tenant_id
        ]

        return True

    def all(self) -> list[TenantPreferences]:

        return list(
            self._preferences.values()
        )

    def clear(self):

        self._preferences.clear()