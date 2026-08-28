from dataclasses import dataclass
from datetime import datetime, time

from heshly_core.models.booking import (
    BookingRequest,
)

from heshly_core.services.booking.staff_assignment import (
    StaffMember,
)


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


def _parse_time(t: str) -> time:
    """Parse HH:MM or HH:MM:SS to time object."""
    if not t:
        raise ValueError("time is required")
    parts = t.strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"invalid time format: {t}")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return time(hour=hour, minute=minute, second=second)


def _minutes_since_midnight(t: time) -> int:
    return t.hour * 60 + t.minute


class AvailabilityChecker:
    """
    Checks whether a requested booking slot
    is available.

    Correctly handles overlapping intervals, not just exact matches.
    """

    def is_available(
        self,
        request: BookingRequest,
        staff: StaffMember | None,
        booked_slots: list[BookedSlot],
    ) -> bool:

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

        for slot in booked_slots:

            # Only check same staff and same date
            if slot.staff != staff.name:
                continue
            if slot.date != request.preferred_date:
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
        request: BookingRequest,
        staff: StaffMember | None,
        booked_slots: list[BookedSlot],
    ) -> BookedSlot | None:
        """Return the first conflicting slot if any."""
        if staff is None or not request.preferred_date or not request.preferred_time:
            return None

        try:
            req_start = _parse_time(request.preferred_time)
        except ValueError:
            return None

        req_duration = request.duration_minutes or 30
        req_start_min = _minutes_since_midnight(req_start)
        req_end_min = req_start_min + req_duration

        for slot in booked_slots:
            if slot.staff != staff.name or slot.date != request.preferred_date:
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
