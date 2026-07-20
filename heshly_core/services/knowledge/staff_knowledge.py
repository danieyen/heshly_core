from typing import Optional

from heshly_core.models.knowledge import (
    KnowledgeContext,
    StaffInfo,
)


class StaffKnowledge:
    """
    Provides staff-related business knowledge.
    """

    def __init__(self, context: KnowledgeContext):
        self.context = context

    def all(self) -> list[StaffInfo]:
        return self.context.staff

    def names(self) -> list[str]:
        return [staff.name for staff in self.context.staff]

    def available(self) -> list[StaffInfo]:
        return [staff for staff in self.context.staff if staff.available]

    def find(self, name: str) -> Optional[StaffInfo]:
        for staff in self.context.staff:
            if staff.name.lower() == name.lower():
                return staff
        return None

    def exists(self, name: str) -> bool:
        return self.find(name) is not None