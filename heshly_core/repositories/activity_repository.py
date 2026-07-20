from __future__ import annotations

from heshly_core.models.crm import (
    CRMActivity,
    ActivityType,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class ActivityRepository(BaseRepository[CRMActivity]):
    """
    In-memory Activity Repository.

    Stores CRM activities such as:
    - Calls
    - Emails
    - WhatsApp messages
    - Meetings
    - Notes
    - Tasks

    This repository can later be replaced by an
    ERPNext implementation without changing the
    ActivityManager.
    """

    def __init__(self):

        self._storage: dict[str, CRMActivity] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        entity: CRMActivity,
    ) -> CRMActivity:

        self._storage[
            entity.activity_id
        ] = entity

        return entity

    def get(
        self,
        entity_id: str,
    ) -> CRMActivity | None:

        return self._storage.get(entity_id)

    def list(self) -> list[CRMActivity]:

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
    ) -> list[CRMActivity]:

        return [

            activity

            for activity in self._storage.values()

            if (
                activity.related_type == related_type
                and
                activity.related_id == related_id
            )

        ]

    def find_by_type(
        self,
        activity_type: ActivityType,
    ) -> list[CRMActivity]:

        return [

            activity

            for activity in self._storage.values()

            if activity.activity_type == activity_type

        ]

    def find_by_user(
        self,
        performed_by: str,
    ) -> list[CRMActivity]:

        return [

            activity

            for activity in self._storage.values()

            if activity.performed_by == performed_by

        ]

    def search(
        self,
        query: str,
    ) -> list[CRMActivity]:

        query = query.lower()

        results: list[CRMActivity] = []

        for activity in self._storage.values():

            if query in activity.description.lower():

                results.append(activity)

                continue

            if (
                activity.performed_by
                and
                query in activity.performed_by.lower()
            ):

                results.append(activity)

                continue

            if (
                query
                in activity.related_type.lower()
            ):

                results.append(activity)

        return results

    # =====================================================
    # Analytics
    # =====================================================

    def count_by_type(
        self,
        activity_type: ActivityType,
    ) -> int:

        return len(
            self.find_by_type(activity_type)
        )

    def count_by_related(
        self,
        related_type: str,
        related_id: str,
    ) -> int:

        return len(

            self.find_by_related(

                related_type,

                related_id,

            )

        )

    def latest(
        self,
        limit: int = 10,
    ) -> list[CRMActivity]:

        return sorted(

            self._storage.values(),

            key=lambda a: a.performed_at,

            reverse=True,

        )[:limit]