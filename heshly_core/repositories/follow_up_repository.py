from __future__ import annotations

from datetime import datetime, UTC

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpStatus,
    FollowUpType,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class FollowUpRepository(BaseRepository[FollowUp]):
    """
    In-memory Follow-up Repository.

    Responsible for storing and querying FollowUp
    records. The implementation can later be replaced
    with an ERPNext/Frappe repository without changing
    the FollowUpManager.
    """

    def __init__(self):

        self._storage: dict[str, FollowUp] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        entity: FollowUp,
    ) -> FollowUp:

        self._storage[
            entity.follow_up_id
        ] = entity

        return entity

    def get(
        self,
        entity_id: str,
    ) -> FollowUp | None:

        return self._storage.get(entity_id)

    def list(self) -> list[FollowUp]:

        return list(
            self._storage.values()
        )

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        if entity_id not in self._storage:
            return False

        del self._storage[entity_id]

        return True

    # =====================================================
    # Utilities
    # =====================================================

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        return entity_id in self._storage

    def count(self) -> int:

        return len(self._storage)

    def clear(self) -> None:

        self._storage.clear()

    # =====================================================
    # Queries
    # =====================================================

    def find_by_related(
        self,
        related_type: str,
        related_id: str,
    ) -> list[FollowUp]:

        return [

            follow_up

            for follow_up in self._storage.values()

            if (
                follow_up.related_type == related_type
                and
                follow_up.related_id == related_id
            )

        ]

    def find_by_status(
        self,
        status: FollowUpStatus,
    ) -> list[FollowUp]:

        return [

            follow_up

            for follow_up in self._storage.values()

            if follow_up.status == status

        ]

    def find_by_type(
        self,
        follow_up_type: FollowUpType,
    ) -> list[FollowUp]:

        return [

            follow_up

            for follow_up in self._storage.values()

            if (
                follow_up.follow_up_type
                == follow_up_type
            )

        ]

    def find_by_assignee(
        self,
        assigned_to: str,
    ) -> list[FollowUp]:

        return [

            follow_up

            for follow_up in self._storage.values()

            if follow_up.assigned_to == assigned_to

        ]

    def due(
        self,
        current_time: datetime | None = None,
    ) -> list[FollowUp]:

        if current_time is None:

            current_time = datetime.now(UTC)

        return [

            follow_up

            for follow_up in self._storage.values()

            if (
                follow_up.status
                == FollowUpStatus.PENDING
                and
                follow_up.scheduled_for
                <= current_time
            )

        ]

    def overdue(
        self,
        current_time: datetime | None = None,
    ) -> list[FollowUp]:

        return self.due(current_time)

    def search(
        self,
        query: str,
    ) -> list[FollowUp]:

        query = query.lower()

        results: list[
            FollowUp
        ] = []

        for follow_up in self._storage.values():

            if (
                query
                in follow_up.subject.lower()
            ):

                results.append(
                    follow_up
                )

                continue

            if (
                follow_up.description
                and
                query
                in follow_up.description.lower()
            ):

                results.append(
                    follow_up
                )

                continue

            if (
                follow_up.assigned_to
                and
                query
                in follow_up.assigned_to.lower()
            ):

                results.append(
                    follow_up
                )

        return results

    # =====================================================
    # Analytics
    # =====================================================

    def count_by_status(
        self,
        status: FollowUpStatus,
    ) -> int:

        return len(
            self.find_by_status(status)
        )

    def count_by_type(
        self,
        follow_up_type: FollowUpType,
    ) -> int:

        return len(
            self.find_by_type(follow_up_type)
        )

    def latest(
        self,
        limit: int = 10,
    ) -> list[FollowUp]:

        return sorted(

            self._storage.values(),

            key=lambda follow_up: (
                follow_up.created_at
            ),

            reverse=True,

        )[:limit]