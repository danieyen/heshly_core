from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TimelineEvent:

    event_type: str

    title: str

    description: str

    created_at: datetime

    source: object



class TimelineBuilder:
    """
    Combines all CRM activities into a single
    chronological timeline.
    """


    def build(
        self,
        *,
        activities=None,
        notes=None,
        tasks=None,
        calls=None,
        emails=None,
        whatsapp=None,
    ) -> list[TimelineEvent]:


        timeline: list[TimelineEvent] = []


        activities = activities or []
        notes = notes or []
        tasks = tasks or []
        calls = calls or []
        emails = emails or []
        whatsapp = whatsapp or []


        # -----------------------------
        # Activities
        # -----------------------------

        for activity in activities:

            timeline.append(

                TimelineEvent(

                    event_type="activity",

                    title=activity.subject,

                    description=activity.description or "",

                    created_at=activity.created_at,

                    source=activity,

                )

            )


        # -----------------------------
        # Notes
        # -----------------------------

        for note in notes:

            timeline.append(

                TimelineEvent(

                    event_type="note",

                    title=note.title,

                    description=note.content,

                    created_at=note.created_at,

                    source=note,

                )

            )


        # -----------------------------
        # Tasks
        # -----------------------------

        for task in tasks:

            timeline.append(

                TimelineEvent(

                    event_type="task",

                    title=task.title,

                    description=task.status.value,

                    created_at=task.created_at,

                    source=task,

                )

            )


        # -----------------------------
        # Calls
        # -----------------------------

        for call in calls:

            timeline.append(

                TimelineEvent(

                    event_type="call",

                    title=f"{call.direction.value} call",

                    description=call.notes or "",

                    created_at=call.created_at,

                    source=call,

                )

            )


        # -----------------------------
        # Emails
        # -----------------------------

        for email in emails:

            timeline.append(

                TimelineEvent(

                    event_type="email",

                    title=email.subject,

                    description=email.body,

                    created_at=email.created_at,

                    source=email,

                )

            )


        # -----------------------------
        # WhatsApp
        # -----------------------------

        for message in whatsapp:

            timeline.append(

                TimelineEvent(

                    event_type="whatsapp",

                    title=(message.direction.value if hasattr(message.direction, "value") else message.direction),

                    description=message.message,

                    created_at=message.created_at,

                    source=message,

                )

            )


        timeline.sort(
            key=lambda item: item.created_at
        )


        return timeline