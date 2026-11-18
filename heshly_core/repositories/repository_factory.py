from __future__ import annotations

from heshly_core.repositories.lead_repository import (
    LeadRepository,
)
from heshly_core.repositories.opportunity_repository import (
    OpportunityRepository,
)
from heshly_core.repositories.activity_repository import (
    ActivityRepository,
)
from heshly_core.repositories.task_repository import (
    TaskRepository,
)
from heshly_core.repositories.note_repository import (
    NoteRepository,
)
from heshly_core.repositories.follow_up_repository import (
    FollowUpRepository,
)
from heshly_core.repositories.whatsapp_activity_repository import (
    WhatsAppActivityRepository,
)
from heshly_core.repositories.pipeline_repository import (
    PipelineRepository,
)


class RepositoryFactory:
    """
    Central repository factory.
    """

    def __init__(self):
        self._lead_repository = LeadRepository()

        self._opportunity_repository = (
            OpportunityRepository()
        )

        self._activity_repository = (
            ActivityRepository()
        )

        self._task_repository = TaskRepository()

        self._note_repository = NoteRepository()

        self._follow_up_repository = (
            FollowUpRepository()
        )

        self._whatsapp_activity_repository = (
            WhatsAppActivityRepository()
        )

        self._pipeline_repository = (
            PipelineRepository()
        )

    # =====================================================
    # Lead
    # =====================================================

    @property
    def leads(self) -> LeadRepository:
        return self._lead_repository

    # =====================================================
    # Opportunity
    # =====================================================

    @property
    def opportunities(
        self,
    ) -> OpportunityRepository:
        return self._opportunity_repository

    # =====================================================
    # Activity
    # =====================================================

    @property
    def activities(
        self,
    ) -> ActivityRepository:
        return self._activity_repository

    # =====================================================
    # Task
    # =====================================================

    @property
    def tasks(self) -> TaskRepository:
        return self._task_repository

    # =====================================================
    # Note
    # =====================================================

    @property
    def notes(self) -> NoteRepository:
        return self._note_repository

    # =====================================================
    # Follow-up
    # =====================================================

    @property
    def follow_ups(
        self,
    ) -> FollowUpRepository:
        return self._follow_up_repository

    # =====================================================
    # WhatsApp Activity
    # =====================================================

    @property
    def whatsapp_activities(
        self,
    ) -> WhatsAppActivityRepository:
        return self._whatsapp_activity_repository

    # =====================================================
    # Pipeline
    # =====================================================

    @property
    def pipelines(
        self,
    ) -> PipelineRepository:
        return self._pipeline_repository

    # =====================================================
    # Utilities
    # =====================================================

    def clear(self) -> None:
        self._opportunity_repository.clear()
        self._lead_repository.clear()
        self._activity_repository.clear()
        self._task_repository.clear()
        self._note_repository.clear()
        self._follow_up_repository.clear()
        self._whatsapp_activity_repository.clear()
        self._pipeline_repository.clear()

    def summary(self) -> dict:
        return {
            "leads": self._lead_repository.count(),
            "opportunities": (
                self._opportunity_repository.count()
            ),
            "activities": (
                self._activity_repository.count()
            ),
            "tasks": self._task_repository.count(),
            "notes": self._note_repository.count(),
            "follow_ups": (
                self._follow_up_repository.count()
            ),
            "whatsapp_activities": (
                self._whatsapp_activity_repository.count()
            ),
            "pipelines": (
                self._pipeline_repository.count()
            ),
        }


repository_factory = RepositoryFactory()
