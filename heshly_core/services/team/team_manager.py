from __future__ import annotations

from heshly_core.models.team_member import (
    TeamMember,
)

from heshly_core.repositories.team_repository import (
    TeamRepository,
)


class TeamManager:
    """
    Team Manager.

    Coordinates business team operations.

    Future:
    - Department management
    - Scheduling integration
    - CRM ownership
    - Calendar assignment
    """


    def __init__(self):

        self.repository = TeamRepository()


    # =====================================================
    # CRUD
    # =====================================================

    def create(
        self,
        member: TeamMember,
    ) -> TeamMember:

        self.repository.save(member)

        return member


    def get(
        self,
        member_id: str,
    ) -> TeamMember | None:

        return self.repository.get(member_id)


    def all(self) -> list[TeamMember]:

        return self.repository.all()


    def delete(
        self,
        member_id: str,
    ) -> None:

        self.repository.delete(member_id)


    # =====================================================
    # Business Queries
    # =====================================================

    def by_business(
        self,
        business_id: str,
    ) -> list[TeamMember]:

        return [
            member
            for member in self.repository.all()
            if member.business_id == business_id
        ]


    # =====================================================
    # Lifecycle
    # =====================================================

    def activate(
        self,
        member_id: str,
    ) -> TeamMember:

        member = self._require(member_id)

        member.activate()

        self.repository.save(member)

        return member


    def deactivate(
        self,
        member_id: str,
    ) -> TeamMember:

        member = self._require(member_id)

        member.deactivate()

        self.repository.save(member)

        return member


    def suspend(
        self,
        member_id: str,
    ) -> TeamMember:

        member = self._require(member_id)

        member.suspend()

        self.repository.save(member)

        return member


    def mark_leave(
        self,
        member_id: str,
    ) -> TeamMember:

        member = self._require(member_id)

        member.mark_leave()

        self.repository.save(member)

        return member


    # =====================================================
    # Helpers
    # =====================================================

    def _require(
        self,
        member_id: str,
    ) -> TeamMember:

        member = self.repository.get(member_id)

        if member is None:
            raise ValueError(
                f"Team member '{member_id}' not found."
            )

        return member


    def summary(self) -> dict:

        members = self.repository.all()

        return {
            "members": len(members),
            "active": sum(
                1 for member in members
                if member.is_active
            ),
        }


    def health(self) -> dict:

        return {
            "service": "team_manager",
            "status": "healthy",
        }