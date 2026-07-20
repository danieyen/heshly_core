from __future__ import annotations

from heshly_core.models.team_member import (
    TeamMember,
)


class TeamRepository:
    """
    Shared Team Repository.

    Stores business team members.

    Future:
        • ERPNext DocTypes
        • MariaDB persistence
        • Tenant isolation
    """

    _members: dict[str, TeamMember] = {}

    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        member: TeamMember,
    ) -> TeamMember:

        self._members[
            member.member_id
        ] = member

        return member

    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        member_id: str,
    ) -> TeamMember | None:

        return self._members.get(
            member_id
        )

    # =====================================================
    # List
    # =====================================================

    def all(self) -> list[TeamMember]:

        return list(
            self._members.values()
        )

    # =====================================================
    # Business Members
    # =====================================================

    def by_business(
        self,
        business_id: str,
    ) -> list[TeamMember]:

        return [

            member

            for member in self._members.values()

            if member.business_id == business_id

        ]

    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        member_id: str,
    ):

        self._members.pop(
            member_id,
            None,
        )

    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self._members.clear()

    # =====================================================
    # Count
    # =====================================================

    def count(self) -> int:

        return len(
            self._members
        )

    # =====================================================
    # Summary
    # =====================================================

    def summary(self) -> dict:

        return {

            "members":
                self.count(),

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "repository":
                "team_repository",

            "status":
                "healthy",

            "records":
                self.count(),

        }