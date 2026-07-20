from __future__ import annotations

from heshly_core.models.user import (
    User,
    UserStatus,
)

from heshly_core.models.team_member import (
    TeamMember,
)

from heshly_core.models.user_invitation import (
    InvitationStatus,
    UserInvitation,
)


class UserActivationFlow:
    """
    User Activation Flow.

    Converts an accepted invitation into
    an active Heshly user.
    """

    def activate(
        self,
        invitation: UserInvitation,
        user: User,
        member: TeamMember,
    ) -> User:

        if invitation.status != InvitationStatus.ACCEPTED:
            raise ValueError(
                "Invitation must be accepted before activation."
            )

        user.activate()

        member.activate()

        return user

    # =====================================================
    # Validation
    # =====================================================

    def can_activate(
        self,
        invitation: UserInvitation,
    ) -> bool:

        return (
            invitation.status
            ==
            InvitationStatus.ACCEPTED
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {
            "service": "user_activation_flow",
            "status": "healthy",
        }