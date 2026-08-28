from dataclasses import dataclass
from datetime import datetime, time, date
from typing import Any

from heshly_core.models.booking import (
    BookingRequest,
)

from heshly_core.services.booking.staff_assignment import (
    StaffMember,
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


@dataclass(slots=True)
class BookedSlot:
    """
    Represents an existing appointment.
    Times are stored as strings (HH:MM) for n8n compatibility,
    but overlap logic handles duration correctly.
    """

    staff: str

    date: str

    time: str

    duration_minutes: int = 30

    @classmethod
    def from_dict(cls, data: Any) -> "BookedSlot":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("BookedSlot data must be dict")
        # Handle n8n sending start as ISO
        if "start" in data and isinstance(data["start"], str):
            try:
                dt = datetime.fromisoformat(data["start"].replace("Z", "+00:00"))
                return cls(
                    staff=str(data.get("staff") or data.get("staff_name") or ""),
                    date=dt.date().isoformat(),
                    time=dt.time().strftime("%H:%M"),
                    duration_minutes=int(data.get("duration_minutes") or data.get("duration") or 30),
                )
            except Exception:
                pass
        return cls(
            staff=str(data.get("staff") or ""),
            date=str(data.get("date") or ""),
            time=str(data.get("time") or ""),
            duration_minutes=int(data.get("duration_minutes") or 30),
        )


def _parse_time(t: str) -> time:
    """Parse HH:MM or HH:MM:SS to time object."""
    if not t:
        raise ValueError("time is required")
    t = str(t).strip()
    # Handle ISO datetime - extract time part
    if "T" in t:
        try:
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            return dt.time()
        except Exception:
            pass
    parts = t.strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"invalid time format: {t}")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return time(hour=hour, minute=minute, second=second)


def _minutes_since_midnight(t: time) -> int:
    return t.hour * 60 + t.minute


def _normalize_request(request: Any) -> BookingRequest:
    """Handle n8n sending dict, JSON string, or nested body."""
    if isinstance(request, BookingRequest):
        return request
    if isinstance(request, dict) or isinstance(request, str):
        # Handle n8n $json.body nesting
        data = _parse_json_if_string(request)
        if isinstance(data, dict):
            if "body" in data and isinstance(data["body"], dict) and "customer_id" in data["body"]:
                data = data["body"]
            if "json" in data and isinstance(data["json"], dict) and "customer_id" in data["json"]:
                data = data["json"]
            return BookingRequest.from_dict(data)
    raise ValueError(f"Invalid booking request: {request}")


def _normalize_slots(slots: Any) -> list[BookedSlot]:
    if slots is None:
        return []
    if isinstance(slots, str):
        import json
        try:
            slots = json.loads(slots)
        except Exception:
            return []
    if not isinstance(slots, list):
        return []
    result = []
    for s in slots:
        if isinstance(s, BookedSlot):
            result.append(s)
        elif isinstance(s, dict):
            try:
                result.append(BookedSlot.from_dict(s))
            except Exception:
                continue
    return result


class AvailabilityChecker:
    """
    Checks whether a requested booking slot
    is available.

    Correctly handles overlapping intervals, not just exact matches.
    Tolerant to n8n sending JSON strings, nested bodies, and ISO datetimes.
    """

    def is_available(
        self,
        request: Any,
        staff: StaffMember | None,
        booked_slots: list[BookedSlot] | Any,
    ) -> bool:

        try:
            request = _normalize_request(request)
        except Exception:
            return False

        booked_slots = _normalize_slots(booked_slots)

        if staff is None:
            return False

        if not request.preferred_date:
            return False

        if not request.preferred_time:
            return False

        # Validate time format early
        try:
            req_start = _parse_time(request.preferred_time)
        except ValueError:
            return False

        req_duration = request.duration_minutes or 30
        req_start_min = _minutes_since_midnight(req_start)
        req_end_min = req_start_min + req_duration

        # Normalize date for comparison (handle both string and date)
        req_date_str = str(request.preferred_date).split("T")[0] if request.preferred_date else ""

        for slot in booked_slots:

            # Only check same staff and same date
            if slot.staff != staff.name:
                continue
            slot_date_str = str(slot.date).split("T")[0] if slot.date else ""
            if slot_date_str != req_date_str:
                continue

            try:
                slot_start = _parse_time(slot.time)
            except ValueError:
                continue

            slot_duration = slot.duration_minutes or 30
            slot_start_min = _minutes_since_midnight(slot_start)
            slot_end_min = slot_start_min + slot_duration

            # Overlap detection: [req_start, req_end) overlaps [slot_start, slot_end)
            overlaps = req_start_min < slot_end_min and req_end_min > slot_start_min
            if overlaps:
                return False

        return True

    def find_conflicting_slot(
        self,
        request: Any,
        staff: StaffMember | None,
        booked_slots: list[BookedSlot] | Any,
    ) -> BookedSlot | None:
        """Return the first conflicting slot if any."""
        try:
            request = _normalize_request(request)
        except Exception:
            return None
        booked_slots = _normalize_slots(booked_slots)
        if staff is None or not request.preferred_date or not request.preferred_time:
            return None

        try:
            req_start = _parse_time(request.preferred_time)
        except ValueError:
            return None

        req_duration = request.duration_minutes or 30
        req_start_min = _minutes_since_midnight(req_start)
        req_end_min = req_start_min + req_duration
        req_date_str = str(request.preferred_date).split("T")[0] if request.preferred_date else ""

        for slot in booked_slots:
            if slot.staff != staff.name:
                continue
            slot_date_str = str(slot.date).split("T")[0] if slot.date else ""
            if slot_date_str != req_date_str:
                continue
            try:
                slot_start = _parse_time(slot.time)
            except ValueError:
                continue
            slot_duration = slot.duration_minutes or 30
            slot_start_min = _minutes_since_midnight(slot_start)
            slot_end_min = slot_start_min + slot_duration
            if req_start_min < slot_end_min and req_end_min > slot_start_min:
                return slot
        return None

    def check_availability_dict(self, request: Any, staff: Any, booked_slots: Any) -> dict:
        """
        n8n-friendly wrapper that always returns {available: bool, reason: str}
        Handles JSON strings and nested bodies.
        """
        try:
            available = self.is_available(request, staff, booked_slots)
            return {
                "available": bool(available),
                "reason": "Slot is available" if available else "Slot conflicts with existing booking",
            }
        except Exception as e:
            return {
                "available": False,
                "reason": f"Availability check failed: {e}",
            }
