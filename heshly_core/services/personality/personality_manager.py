from heshly_core.models.personality import (
    PersonalityProfile,
)

from heshly_core.services.personality.personality_conversation_flow import (
    PersonalityConversationFlow,
)


class PersonalityManager:
    """
    Central manager for receptionist personalities.

    Responsible for:

    • registering personalities
    • selecting the active personality
    • retrieving personalities
    • building prompt instructions
    """

    def __init__(self):

        self._profiles: dict[
            str,
            PersonalityProfile,
        ] = {}

        self._active_profile: str | None = None

        self._flow = (
            PersonalityConversationFlow()
        )

    def register(
        self,
        profile: PersonalityProfile,
    ) -> None:
        """
        Registers a personality profile.
        """

        self._profiles[
            profile.name
        ] = profile

        if self._active_profile is None:

            self._active_profile = (
                profile.name
            )

    def activate(
        self,
        profile_name: str,
    ) -> None:
        """
        Sets the active personality.
        """

        if profile_name not in self._profiles:

            raise ValueError(
                f"Unknown personality: "
                f"{profile_name}"
            )

        self._active_profile = (
            profile_name
        )

    def active_profile(
        self,
    ) -> PersonalityProfile:
        """
        Returns the currently active profile.
        """

        if self._active_profile is None:

            raise ValueError(
                "No active personality."
            )

        return self._profiles[
            self._active_profile
        ]

    def personalities(
        self,
    ) -> list[str]:
        """
        Returns registered personalities.
        """

        return sorted(
            self._profiles.keys()
        )

    def build(
        self,
    ) -> dict:
        """
        Builds the active personality
        instruction bundle.
        """

        profile = self.active_profile()

        return self._flow.execute(
            profile
        )