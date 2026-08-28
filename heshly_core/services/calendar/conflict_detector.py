from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from heshly_core.models.calendar import (
    AppointmentRequest,
    CalendarEvent,
    AppointmentStatus,
)


def _parse_json_if_string(value: Any) -> Any:
    if isinstance(value, str):
        import json
        value = value.strip()
        if value.startswith("{") and value.endswith("}"):
            try:
                return json.loads(value)
            except Exception:
                return value
        if value.startswith("[") and value.endswith("]"):
            try:
                return json.loads(value)
            except Exception:
                return value
    return value


@dataclass(slots=True)
class ConflictResult:
    """
    Result of conflict analysis.
    """

    has_conflict: bool

    message: str = ""

    conflicting_event: CalendarEvent | None = None

    def to_dict(self) -> dict:
        return {
            "has_conflict": bool(self.has_conflict),
            "message": self.message,
            "conflicting_event": self.conflicting_event.event_id if self.conflicting_event else None,
        }


class ConflictDetector:
    """
    Detects scheduling conflicts.

    Handles:
    - time overlaps (exclusive end)
    - cancelled/completed events are ignored
    - optional staff filtering if request notes contain staff
    Tolerant to n8n sending JSON strings and nested bodies.
    """

    def detect(
        self,
        request: Any,
        events: list[CalendarEvent] | Any,
    ) -> ConflictResult:

        # Normalize request
        if isinstance(request, dict) or isinstance(request, str):
            data = _parse_json_if_string(request)
            if isinstance(data, dict):
                if "body" in data and isinstance(data["body"], dict):
                    data = data["body"]
                try:
                    request = AppointmentRequest.from_dict(data)
                except Exception as e:
                    return ConflictResult(
                        has_conflict=True,
                        message=f"Invalid appointment request: {e}",
                    )

        if not isinstance(request, AppointmentRequest):
            return ConflictResult(
                has_conflict=True,
                message="Appointment request is required.",
            )

        if not request.start:
            return ConflictResult(
                has_conflict=True,
                message="Appointment start time is required.",
            )

        if request.duration_minutes <= 0:
            return ConflictResult(
                has_conflict=True,
                message="Invalid appointment duration.",
            )

        # Normalize events
        if isinstance(events, str):
            events = _parse_json_if_string(events)
        if isinstance(events, dict) and "body" in events:
            events = events["body"]
        if not isinstance(events, list):
            events = []

        normalized_events = []
        for e in events:
            if isinstance(e, CalendarEvent):
                normalized_events.append(e)
            elif isinstance(e, dict):
                try:
                    # Handle n8n sending event as dict
                    from datetime import datetime
                    start = e.get("start")
                    end = e.get("end")
                    if isinstance(start, str):
                        start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    if isinstance(end, str):
                        end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    status = e.get("status", "confirmed")
                    if isinstance(status, str):
                        try:
                            status = AppointmentStatus(status)
                        except ValueError:
                            status = AppointmentStatus.CONFIRMED
                    normalized_events.append(CalendarEvent(
                        event_id=str(e.get("event_id") or e.get("eventId") or e.get("id") or ""),
                        title=str(e.get("title") or ""),
                        start=start,
                        end=end,
                        customer_name=e.get("customer_name"),
                        customer_phone=e.get("customer_phone"),
                        notes=e.get("notes"),
                        status=status,
                    ))
                except Exception:
                    continue

        appointment_end = (
            request.start
            + timedelta(
                minutes=request.duration_minutes
            )
        )

        for event in normalized_events:

            # Ignore non-blocking statuses
            if event.status in (AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW):
                continue

            # Basic time overlap: [start, end) overlaps [event.start, event.end)
            overlaps = (

                request.start < event.end

                and

                appointment_end > event.start

            )

            if overlaps:

                return ConflictResult(

                    has_conflict=True,

                    message="Appointment conflicts with an existing booking.",

                    conflicting_event=event,

                )

        return ConflictResult(

            has_conflict=False,

            message="No conflicts detected.",

        )

    def detect_for_staff(
        self,
        request: Any,
        events: list[CalendarEvent] | Any,
        staff_name: str | None = None,
    ) -> ConflictResult:
        """
        Staff-aware conflict detection. If staff_name is provided,
        only events for that staff are considered.
        Handles n8n wrapping and JSON strings.
        """
        # Normalize events first
        if isinstance(events, str):
            events = _parse_json_if_string(events)
        if isinstance(events, dict) and "body" in events:
            events = events["body"]
        if not isinstance(events, list):
            events = []

        # Normalize to CalendarEvent list for filtering
        normalized = []
        for e in events:
            if isinstance(e, CalendarEvent):
                normalized.append(e)
            elif isinstance(e, dict):
                try:
                    from datetime import datetime
                    start = e.get("start")
                    end = e.get("end")
                    if isinstance(start, str):
                        start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    if isinstance(end, str):
                        end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    status = e.get("status", "confirmed")
                    if isinstance(status, str):
                        try:
                            status = AppointmentStatus(status)
                        except ValueError:
                            status = AppointmentStatus.CONFIRMED
                    normalized.append(CalendarEvent(
                        event_id=str(e.get("event_id") or e.get("id") or ""),
                        title=str(e.get("title") or ""),
                        start=start,
                        end=end,
                        customer_name=e.get("customer_name"),
                        customer_phone=e.get("customer_phone"),
                        notes=e.get("notes"),
                        status=status,
                    ))
                except Exception:
                    continue

        if staff_name:
            staff_name = str(staff_name).strip()
            if staff_name:
                filtered = [e for e in normalized if (e.customer_name == staff_name or staff_name.lower() in (e.title or "").lower())]
                # Fallback to all events if filtering yields nothing and title doesn't contain staff
                # To avoid false negatives, if no staff-specific events found, check all
                if not filtered:
                    filtered = normalized
                return self.detect(request, filtered)
        return self.detect(request, normalized)
