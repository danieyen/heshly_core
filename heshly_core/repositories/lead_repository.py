from __future__ import annotations

from heshly_core.models.crm import Lead
from heshly_core.repositories.base_repository import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    """
    In-memory Lead Repository.

    This implementation is intentionally simple.
    Later it can be replaced by an ERPNext repository
    without changing LeadManager.
    """

    def __init__(self):

        self._storage: dict[str, Lead] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        entity: Lead,
    ) -> Lead:

        self._storage[entity.lead_id] = entity

        return entity

    def get(
        self,
        entity_id: str,
    ) -> Lead | None:

        return self._storage.get(entity_id)

    def list(self) -> list[Lead]:

        return list(self._storage.values())

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
    # Lead Queries
    # =====================================================

    def find_by_email(
        self,
        email: str,
    ) -> Lead | None:

        email = email.lower()

        for lead in self._storage.values():

            if (
                lead.email
                and lead.email.lower() == email
            ):
                return lead

        return None

    def find_by_phone(
        self,
        phone: str,
    ) -> Lead | None:

        for lead in self._storage.values():

            if lead.phone == phone:
                return lead

        return None

    def find_by_company(
        self,
        company: str,
    ) -> list[Lead]:

        company = company.lower()

        return [

            lead

            for lead in self._storage.values()

            if (
                lead.company
                and company in lead.company.lower()
            )

        ]

    def find_by_status(
        self,
        status,
    ) -> list[Lead]:

        return [

            lead

            for lead in self._storage.values()

            if lead.status == status

        ]

    def find_by_source(
        self,
        source: str,
    ) -> list[Lead]:

        source = source.lower()

        return [

            lead

            for lead in self._storage.values()

            if lead.source.lower() == source

        ]

    def search(
        self,
        query: str,
    ) -> list[Lead]:

        query = query.lower()

        results: list[Lead] = []

        for lead in self._storage.values():

            if query in lead.full_name.lower():

                results.append(lead)

                continue

            if (
                lead.company
                and query in lead.company.lower()
            ):

                results.append(lead)

                continue

            if (
                lead.email
                and query in lead.email.lower()
            ):

                results.append(lead)

                continue

            if (
                lead.phone
                and query in lead.phone
            ):

                results.append(lead)

        return results