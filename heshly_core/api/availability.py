from __future__ import annotations

from typing import Any
from datetime import datetime, UTC

from heshly_core.models.calendar import AvailabilityResult, TimeSlot
from heshly_core.models.booking import BookingRequest
from heshly_core.services.tenant.tenant_context import TenantContext


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


def _extract_payload(payload: Any) -> dict:
    payload = _parse_json_if_string(payload)
    if isinstance(payload, dict):
        # Handle n8n $json.body and $json.json nesting
        if "body" in payload and isinstance(payload["body"], dict):
            # Check if body looks like the actual request
            body = payload["body"]
            if any(k in body for k in ("service", "preferred_date", "preferred_time", "start", "date", "time")):
                return body
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("service", "preferred_date", "preferred_time", "start")):
                return inner
        if "data" in payload and isinstance(payload["data"], dict):
            return payload["data"]
    if isinstance(payload, dict):
        return payload
    return {}


class AvailabilityAPI:
    """
    Availability API Layer for n8n.

    Provides availability checking with tolerant input handling.
    Always returns {available: bool, slots: [...], reason: str} with boolean.
    Handles:
    - JSON strings vs objects
    - $json.body nesting
    - separate date+time vs ISO start
    - string booleans
    """

    def __init__(self, tenant_context: TenantContext | None = None):
        self.tenant_context = tenant_context or TenantContext()

    def check(self, payload: Any) -> dict:
        """
        Check availability. Accepts BookingRequest shape or AvailabilityRequest shape.
        Returns dict with boolean available - never string.
        """
        data = _extract_payload(payload)

        # Ensure tenant context if provided
        tenant_id = data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        # Try to build BookingRequest from payload
        try:
            request = BookingRequest.from_dict(data)
        except Exception as e:
            return {
                "available": False,
                "slots": [],
                "reason": f"Invalid request: {e}",
            }

        if not request.service:
            return {
                "available": False,
                "slots": [],
                "reason": "service is required",
            }
        if not request.preferred_date or not request.preferred_time:
            return {
                "available": False,
                "slots": [],
                "reason": f"Missing fields: {', '.join(request.missing_fields())}",
            }

        # If n8n already did availability check and sent slots, return them
        if "slots" in data and isinstance(data["slots"], list):
            slots = []
            for s in data["slots"]:
                try:
                    if isinstance(s, dict):
                        start = s.get("start")
                        end = s.get("end")
                        if isinstance(start, str):
                            start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                        if isinstance(end, str):
                            end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                        slots.append(TimeSlot(start=start, end=end, available=bool(s.get("available", True))))
                except Exception:
                    continue
            # If slots provided, available is true if any available
            available = any(s.available for s in slots) if slots else False
            return {
                "available": bool(available),
                "slots": [s.to_dict() for s in slots],
                "reason": "Slots provided" if slots else "No slots provided",
            }

        # Otherwise, we need to check via AvailabilityChecker
        # For now, return available true with generated slots if request is complete
        # Real implementation would query calendar
        try:
            from heshly_core.services.booking.availability_checker import AvailabilityChecker
            from heshly_core.services.booking.staff_assignment import StaffMember

            # Try to get staff
            staff_name = request.preferred_staff or data.get("staff") or "default"
            staff = StaffMember(name=staff_name) if staff_name else None

            # Get booked slots from payload if provided
            booked_slots = data.get("booked_slots") or data.get("bookedSlots") or data.get("events") or []

            checker = AvailabilityChecker()
            available = checker.is_available(request, staff, booked_slots)

            # Generate slots for response
            slots = []
            if available:
                try:
                    date_str = str(request.preferred_date).split("T")[0]
                    time_str = str(request.preferred_time)
                    start = datetime.fromisoformat(f"{date_str}T{time_str}:00").replace(tzinfo=UTC)
                    from datetime import timedelta
                    end = start + timedelta(minutes=request.duration_minutes or 30)
                    slots.append(TimeSlot(start=start, end=end, available=True))
                except Exception:
                    pass

            return {
                "available": bool(available),
                "slots": [s.to_dict() for s in slots],
                "reason": "Slot is available" if available else "Slot conflicts with existing booking",
            }
        except Exception as e:
            return {
                "available": False,
                "slots": [],
                "reason": f"Availability check failed: {e}",
            }

    def check_tolerant(self, payload: Any) -> dict:
        """Alias for check that handles all n8n wrapping."""
        return self.check(payload)

    def health(self) -> dict:
        return {
            "api": "availability_api",
            "status": "healthy",
        }
