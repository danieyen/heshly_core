from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, UTC
from typing import Any

from heshly_core.models.calendar import (
    AppointmentRequest,
    BusinessHours as CalendarBusinessHours,
)


# Backward compatibility: n8n and old code may import BusinessHours from here
# Canonical definition is in heshly_core.models.calendar.BusinessHours
@dataclass(slots=True)
class BusinessHours:
    """
    Business operating hours for a single day.
    For weekly schedules use heshly_core.models.calendar.BusinessHours
    with weekday field. This class is for single-day validation
    as called by n8n availability checks.
    Deprecated: import from heshly_core.models.calendar instead.
    """

    opening_time: time

    closing_time: time

    enabled: bool = True

    def to_calendar_hours(self, weekday: int = 0) -> CalendarBusinessHours:
        return CalendarBusinessHours(
            weekday=weekday,
            opens_at=self.opening_time,
            closes_at=self.closing_time,
            enabled=self.enabled,
        )

    @classmethod
    def from_calendar_hours(cls, ch: CalendarBusinessHours) -> "BusinessHours":
        return cls(
            opening_time=ch.opens_at,
            closing_time=ch.closes_at,
            enabled=ch.enabled,
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
    return value


def _normalize_hours(hours: Any) -> BusinessHours | CalendarBusinessHours:
    """Handle n8n sending dict, JSON string, or either BusinessHours shape."""
    if isinstance(hours, (BusinessHours, CalendarBusinessHours)):
        return hours
    if isinstance(hours, dict) or isinstance(hours, str):
        data = _parse_json_if_string(hours)
        if isinstance(data, dict):
            # Handle n8n $json.body nesting
            if "body" in data and isinstance(data["body"], dict):
                data = data["body"]
            # Detect shape
            if "opens_at" in data or "closes_at" in data:
                # Calendar shape
                opens = data.get("opens_at") or data.get("opening_time") or "09:00"
                closes = data.get("closes_at") or data.get("closing_time") or "17:00"
                if isinstance(opens, str):
                    opens = time.fromisoformat(opens.split("T")[-1].split("+")[0].split("Z")[0])
                if isinstance(closes, str):
                    closes = time.fromisoformat(closes.split("T")[-1].split("+")[0].split("Z")[0])
                return CalendarBusinessHours(
                    weekday=int(data.get("weekday", 0)),
                    opens_at=opens,
                    closes_at=closes,
                    enabled=bool(data.get("enabled", True)),
                )
            else:
                opens = data.get("opening_time") or data.get("opens_at") or "09:00"
                closes = data.get("closing_time") or data.get("closes_at") or "17:00"
                if isinstance(opens, str):
                    opens = time.fromisoformat(opens.split("T")[-1].split("+")[0].split("Z")[0])
                if isinstance(closes, str):
                    closes = time.fromisoformat(closes.split("T")[-1].split("+")[0].split("Z")[0])
                return BusinessHours(
                    opening_time=opens,
                    closing_time=closes,
                    enabled=bool(data.get("enabled", True)),
                )
    raise ValueError(f"Invalid business hours: {hours}")


@dataclass(slots=True)
class BusinessHoursResult:
    """
    Result of business hours validation.
    """

    within_hours: bool

    message: str = ""

    def to_dict(self) -> dict:
        return {
            "within_hours": bool(self.within_hours),
            "message": self.message,
        }


class BusinessHoursManager:
    """
    Validates appointments against
    business operating hours.
    Handles timezone-aware datetimes and disabled days.
    Tolerant to n8n sending JSON strings and either BusinessHours shape.
    """

    def is_within_hours(
        self,
        request: Any,
        hours: Any,
    ) -> BusinessHoursResult:
        """
        Check whether an appointment
        falls within business hours.
        """

        # Normalize request
        if isinstance(request, dict) or isinstance(request, str):
            data = _parse_json_if_string(request)
            if isinstance(data, dict):
                try:
                    request = AppointmentRequest.from_dict(data)
                except Exception:
                    return BusinessHoursResult(
                        within_hours=False,
                        message="Invalid appointment request.",
                    )

        if not isinstance(request, AppointmentRequest):
            return BusinessHoursResult(
                within_hours=False,
                message="Appointment request is required.",
            )

        if not request.start:
            return BusinessHoursResult(
                within_hours=False,
                message="Appointment start time is required.",
            )

        # Normalize hours
        try:
            hours = _normalize_hours(hours)
        except Exception as e:
            return BusinessHoursResult(
                within_hours=False,
                message=f"Invalid business hours: {e}",
            )

        # Extract opening/closing/enabled regardless of shape
        if isinstance(hours, CalendarBusinessHours):
            opening_time = hours.opens_at
            closing_time = hours.closes_at
            enabled = hours.enabled
        else:
            opening_time = hours.opening_time
            closing_time = hours.closing_time
            enabled = hours.enabled

        if not enabled:
            return BusinessHoursResult(
                within_hours=False,
                message="Business is closed on this day.",
            )

        if opening_time >= closing_time:
            return BusinessHoursResult(
                within_hours=False,
                message="Invalid business hours configuration.",
            )

        # Normalize to date of appointment
        # Use UTC if naive, preserve tz if aware
        start = request.start
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)

        appointment_end = (
            start
            + timedelta(
                minutes=request.duration_minutes
            )
        )

        # Build opening/closing on same date with same tz
        opening = datetime.combine(
            start.date(),
            opening_time,
        ).replace(tzinfo=start.tzinfo)

        closing = datetime.combine(
            start.date(),
            closing_time,
        ).replace(tzinfo=start.tzinfo)

        if start < opening:

            return BusinessHoursResult(

                within_hours=False,

                message="Appointment starts before business opens.",
            )

        if appointment_end > closing:

            return BusinessHoursResult(

                within_hours=False,

                message="Appointment ends after business closes.",
            )

        return BusinessHoursResult(

            within_hours=True,

            message="Appointment is within business hours.",
        )

    def validate_weekly(
        self,
        request: AppointmentRequest,
        weekly_hours: list,
    ) -> BusinessHoursResult:
        """
        Validate against weekly schedule (list of calendar.BusinessHours).
        Handles JSON strings and mixed shapes.
        """
        if not weekly_hours:
            return BusinessHoursResult(within_hours=True, message="No weekly hours configured.")

        # Normalize weekly_hours if sent as JSON string
        if isinstance(weekly_hours, str):
            import json
            try:
                weekly_hours = json.loads(weekly_hours)
            except Exception:
                return BusinessHoursResult(within_hours=False, message="Invalid weekly hours format.")

        # Handle n8n wrapping
        if isinstance(weekly_hours, dict) and "body" in weekly_hours:
            weekly_hours = weekly_hours["body"]

        if not isinstance(weekly_hours, list):
            weekly_hours = [weekly_hours]

        normalized = []
        for h in weekly_hours:
            try:
                normalized.append(_normalize_hours(h))
            except Exception:
                continue

        if not normalized:
            return BusinessHoursResult(within_hours=True, message="No weekly hours configured.")

        weekday = request.start.weekday()
        for h in normalized:
            # Get weekday regardless of shape
            h_weekday = h.weekday if isinstance(h, CalendarBusinessHours) else 0
            # For single-day BusinessHours without weekday, assume it applies to requested day
            if isinstance(h, BusinessHours) or h_weekday == weekday:
                if not h.enabled if isinstance(h, BusinessHours) else not h.enabled:
                    return BusinessHoursResult(within_hours=False, message="Business is closed on this day.")
                # Map to local BusinessHours for validation
                if isinstance(h, CalendarBusinessHours):
                    return self.is_within_hours(
                        request,
                        BusinessHours(opening_time=h.opens_at, closing_time=h.closes_at, enabled=h.enabled),
                    )
                else:
                    return self.is_within_hours(request, h)
        return BusinessHoursResult(within_hours=False, message="No business hours defined for this weekday.")
