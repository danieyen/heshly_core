from __future__ import annotations

from heshly_core.services.crm.activity_logger import (
    ActivityLogger,
)

from heshly_core.services.crm.task_manager import (
    TaskManager,
)

from heshly_core.services.crm.note_manager import (
    NoteManager,
)

from heshly_core.services.crm.call_logger import (
    CallLogger,
)

from heshly_core.services.crm.email_logger import (
    EmailLogger,
)

from heshly_core.services.crm.whatsapp_activity_logger import (
    WhatsAppActivityLogger,
)

from heshly_core.services.crm.timeline_builder import (
    TimelineBuilder,
)


class ActivityManager:
    """
    Central CRM Activity Manager.

    Coordinates all activity-related services.
    """

    def __init__(self):

        self.activity_logger = ActivityLogger()

        self.task_manager = TaskManager()

        self.note_manager = NoteManager()

        self.call_logger = CallLogger()

        self.email_logger = EmailLogger()

        self.whatsapp_logger = (
            WhatsAppActivityLogger()
        )

        self.timeline_builder = (
            TimelineBuilder()
        )

    # --------------------------------------------------
    # Activities
    # --------------------------------------------------

    def log_activity(self, **kwargs):

        return self.activity_logger.log(**kwargs)

    # --------------------------------------------------
    # Tasks
    # --------------------------------------------------

    def create_task(self, **kwargs):

        return self.task_manager.create_task(
            **kwargs
        )

    def complete_task(self, task_id):

        return self.task_manager.complete_task(
            task_id
        )

    # --------------------------------------------------
    # Notes
    # --------------------------------------------------

    def create_note(self, **kwargs):

        return self.note_manager.create_note(
            **kwargs
        )

    # --------------------------------------------------
    # Calls
    # --------------------------------------------------

    def log_call(self, **kwargs):

        return self.call_logger.log_call(
            **kwargs
        )

    # --------------------------------------------------
    # Emails
    # --------------------------------------------------

    def log_email(self, **kwargs):

        return self.email_logger.log_email(
            **kwargs
        )

    # --------------------------------------------------
    # WhatsApp
    # --------------------------------------------------

    def log_whatsapp(self, **kwargs):

        return self.whatsapp_logger.log_message(
            **kwargs
        )

    # --------------------------------------------------
    # Timeline
    # --------------------------------------------------

    def build_timeline(
        self,
        *,
        activities=None,
        notes=None,
        tasks=None,
        calls=None,
        emails=None,
        whatsapp=None,
    ):

        return self.timeline_builder.build(

            activities=activities,

            notes=notes,

            tasks=tasks,

            calls=calls,

            emails=emails,

            whatsapp=whatsapp,
        )