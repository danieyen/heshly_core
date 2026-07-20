from __future__ import annotations

from heshly_core.models.user_invitation import (
    UserInvitation,
)


class UserInvitationManager:
    """
    In-memory invitation manager.

    Future:
    - Email delivery
    - WhatsApp invitations
    - Secure invitation tokens
    - ERPNext persistence
    """

    _invitations: dict[str, UserInvitation] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def create(
        self,
        invitation: UserInvitation,
    ) -> UserInvitation:

        self._invitations[
            invitation.invitation_id
        ] = invitation

        return invitation


    def get(
        self,
        invitation_id: str,
    ) -> UserInvitation | None:

        return self._invitations.get(
            invitation_id
        )


    def all(self) -> list[UserInvitation]:

        return list(
            self._invitations.values()
        )


    # =====================================================
    # Lifecycle
    # =====================================================

    def accept(
        self,
        invitation_id: str,
    ) -> UserInvitation:

        invitation = self._require(
            invitation_id
        )

        invitation.accept()

        return invitation


    def decline(
        self,
        invitation_id: str,
    ) -> UserInvitation:

        invitation = self._require(
            invitation_id
        )

        invitation.decline()

        return invitation


    def expire(
        self,
        invitation_id: str,
    ) -> UserInvitation:

        invitation = self._require(
            invitation_id
        )

        invitation.expire()

        return invitation


    # =====================================================
    # Helpers
    # =====================================================

    def _require(
        self,
        invitation_id: str,
    ) -> UserInvitation:

        invitation = self.get(
            invitation_id
        )

        if invitation is None:
            raise ValueError(
                f"Invitation '{invitation_id}' not found."
            )

        return invitation


    def clear(self):

        self._invitations.clear()


    def health(self):

        return {
            "service": "user_invitation_manager",
            "status": "healthy",
            "invitations": len(self._invitations),
        }