from __future__ import annotations

from heshly_core.models.business_profile import (
    BusinessProfile,
)

from heshly_core.models.business_settings import (
    BusinessSettings,
)


class BusinessConfigurationRepository:
    """
    Stores business configuration.

    Handles:

    - Business profile storage
    - Business settings storage

    Future:

    - ERPNext DocTypes
    - MariaDB persistence
    - Configuration versioning
    """


    def __init__(self):

        self._profiles: dict[str, BusinessProfile] = {}

        self._settings: dict[str, BusinessSettings] = {}



    # =====================================================
    # Profile Storage
    # =====================================================

    def save_profile(
        self,
        profile: BusinessProfile,
    ) -> BusinessProfile:


        self._profiles[
            profile.business_id
        ] = profile


        return profile



    def get_profile(
        self,
        business_id: str,
    ) -> BusinessProfile | None:


        return self._profiles.get(
            business_id
        )



    # =====================================================
    # Settings Storage
    # =====================================================

    def save_settings(
        self,
        settings: BusinessSettings,
    ) -> BusinessSettings:


        self._settings[
            settings.business_id
        ] = settings


        return settings



    def get_settings(
        self,
        business_id: str,
    ) -> BusinessSettings | None:


        return self._settings.get(
            business_id
        )



    # =====================================================
    # Configuration
    # =====================================================

    def get_configuration(
        self,
        business_id: str,
    ) -> dict:


        return {

            "profile":
                self.get_profile(
                    business_id
                ),

            "settings":
                self.get_settings(
                    business_id
                ),

        }



    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        business_id: str,
    ):


        self._profiles.pop(
            business_id,
            None,
        )


        self._settings.pop(
            business_id,
            None,
        )



    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self._profiles.clear()

        self._settings.clear()



    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "business_configuration_repository",

            "status":
                "healthy",

            "profiles":
                len(self._profiles),

            "settings":
                len(self._settings),

        }