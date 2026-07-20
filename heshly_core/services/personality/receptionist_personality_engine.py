from heshly_core.models.personality import (
    PersonalityProfile,
)

from heshly_core.services.personality.personality_manager import (
    PersonalityManager,
)


class ReceptionistPersonalityEngine:
    """
    Public entry point for the receptionist
    personality subsystem.
    """

    def __init__(self):

        self.manager = PersonalityManager()

    def register_personality(
        self,
        profile: PersonalityProfile,
    ) -> None:
        """
        Register a new receptionist personality.
        """

        self.manager.register(profile)

    def activate_personality(
        self,
        profile_name: str,
    ) -> None:
        """
        Activate a registered personality.
        """

        self.manager.activate(profile_name)

    def available_personalities(
        self,
    ) -> list[str]:
        """
        Return all registered personalities.
        """

        return self.manager.personalities()

    def active_personality(
        self,
    ) -> PersonalityProfile:
        """
        Return the active personality profile.
        """

        return self.manager.active_profile()

    def build_personality_bundle(
        self,
    ) -> dict:
        """
        Build the personality instruction bundle
        for the active receptionist.
        """

        return self.manager.build()