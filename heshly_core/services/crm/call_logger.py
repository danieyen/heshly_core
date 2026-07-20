from __future__ import annotations

import uuid

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CallDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallOutcome(str, Enum):
    ANSWERED = "answered"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    BUSY = "busy"
    CALLBACK_REQUESTED = "callback_requested"
    COMPLETED = "completed"


@dataclass(slots=True)
class CallLog:

    call_id: str

    business_id: str

    related_type: str

    related_id: str

    direction: CallDirection

    phone_number: str

    duration_seconds: int = 0

    outcome: CallOutcome = CallOutcome.COMPLETED

    notes: str | None = None

    logged_by: str | None = None

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


class CallLoggingError(Exception):
    pass


class CallLogger:

    def __init__(self):

        self.calls: list[CallLog] = []


    def log_call(
        self,
        business_id: str,
        related_type: str,
        related_id: str,
        direction: CallDirection,
        phone_number: str,
        duration_seconds: int = 0,
        outcome: CallOutcome = CallOutcome.COMPLETED,
        notes: str | None = None,
        logged_by: str | None = None,
    ) -> CallLog:

        if not business_id:
            raise CallLoggingError(
                "Business ID is required."
            )

        if not related_id:
            raise CallLoggingError(
                "Related ID is required."
            )

        if not phone_number.strip():
            raise CallLoggingError(
                "Phone number is required."
            )

        if duration_seconds < 0:
            raise CallLoggingError(
                "Duration cannot be negative."
            )

        call = CallLog(

            call_id=self._generate_id(),

            business_id=business_id,

            related_type=related_type,

            related_id=related_id,

            direction=direction,

            phone_number=phone_number,

            duration_seconds=duration_seconds,

            outcome=outcome,

            notes=notes,

            logged_by=logged_by,

        )

        self.calls.append(call)

        return call


    def get_calls(
        self,
        related_type: str,
        related_id: str,
    ) -> list[CallLog]:

        return [

            call

            for call in self.calls

            if (
                call.related_type == related_type
                and
                call.related_id == related_id
            )

        ]


    def _generate_id(self):

        return (
            f"CALL-{uuid.uuid4().hex[:8].upper()}"
        )