from __future__ import annotations

from typing import Any
from datetime import datetime, UTC, date

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
        # Handle n8n $json.body and $json.json and $json.data nesting
        # Also handle capitalized Business/Entities
        if "body" in payload and isinstance(payload["body"], dict):
            body = payload["body"]
            if any(k in body for k in ("service", "preferred_date", "preferred_time", "start", "date", "time", "Business", "Entities", "business", "entities", "tenant_id", "tenantId")):
                return body
            if "data" in body and isinstance(body["data"], dict):
                return body["data"]
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("service", "preferred_date", "preferred_time", "start", "Business", "Entities")):
                return inner
        if "data" in payload and isinstance(payload["data"], dict):
            inner = payload["data"]
            # data wrapper from Execute Workflow - may contain Business/Entities capitalized
            if any(k in inner for k in ("Business", "Entities", "business", "entities", "service", "tenant_id")):
                return inner
            return inner
        # Handle direct capitalized keys at top level
        if any(k in payload for k in ("Business", "Entities")):
            # normalize to lowercase for downstream but keep original
            return payload
    if isinstance(payload, dict):
        return payload
    return {}


def _get_nested(data: dict, *keys) -> Any:
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return None


def _resolve_service(data: dict) -> str | None:
    # direct
    for k in ("service", "Service"):
        if k in data and isinstance(data[k], str) and data[k].strip():
            return data[k].strip()
    # entities lowercase
    for ekey in ("entities", "Entities"):
        if ekey in data and isinstance(data[ekey], dict):
            for sk in ("service", "Service", "service_name"):
                if sk in data[ekey] and isinstance(data[ekey][sk], str) and data[ekey][sk].strip():
                    return data[ekey][sk].strip()
    # also check nested data
    return None


def _resolve_date(data: dict) -> str | None:
    for k in ("preferred_date", "date", "Date"):
        if k in data and data[k]:
            return str(data[k]).strip()
    for ekey in ("entities", "Entities"):
        if ekey in data and isinstance(data[ekey], dict):
            for dk in ("preferred_date", "date", "Date", "scheduled_time"):
                if dk in data[ekey] and data[ekey][dk]:
                    v = str(data[ekey][dk]).strip()
                    if "T" in v:
                        v = v.split("T")[0]
                    return v
    # scheduled_time at top
    if "scheduled_time" in data and data["scheduled_time"]:
        v = str(data["scheduled_time"]).strip()
        if "T" in v:
            return v.split("T")[0]
    return None


def _resolve_time(data: dict) -> str | None:
    for k in ("preferred_time", "time", "Time"):
        if k in data and data[k]:
            return str(data[k]).strip()
    for ekey in ("entities", "Entities"):
        if ekey in data and isinstance(data[ekey], dict):
            for tk in ("preferred_time", "time", "Time", "scheduled_time"):
                if tk in data[ekey] and data[ekey][tk]:
                    v = str(data[ekey][tk]).strip()
                    if "T" in v:
                        # extract time part
                        try:
                            v = v.split("T")[1].split(".")[0].split("Z")[0].split("+")[0]
                            return v[:5] if len(v) >= 5 else v
                        except Exception:
                            return v
                    return v
    if "scheduled_time" in data and data["scheduled_time"]:
        v = str(data["scheduled_time"]).strip()
        if "T" in v:
            try:
                t = v.split("T")[1].split(".")[0].split("Z")[0].split("+")[0]
                return t[:5] if len(t) >= 5 else t
            except Exception:
                pass
    return None


def _resolve_tenant_id(data: dict) -> str | None:
    for k in ("tenant_id", "tenantId"):
        if k in data and isinstance(data[k], str) and data[k].strip() and data[k].strip() != "heshly":
            return data[k].strip()
        if k in data and isinstance(data[k], str) and data[k].strip():
            # allow heshly if explicitly set but prefer real tenant
            return data[k].strip()
    for bkey in ("business", "Business"):
        if bkey in data and isinstance(data[bkey], dict):
            b = data[bkey]
            for tk in ("tenant_id", "tenantId", "id", "business_id"):
                if tk in b and isinstance(b[tk], str) and b[tk].strip() and b[tk].strip() != "heshly":
                    return b[tk].strip()
            for tk in ("tenant_id", "tenantId", "id"):
                if tk in b and isinstance(b[tk], str) and b[tk].strip():
                    return b[tk].strip()
    # also check nested entities/business
    return None


def _resolve_duration(data: dict) -> int | None:
    for k in ("duration_minutes", "duration", "Duration"):
        if k in data and data[k] is not None:
            try:
                return int(data[k])
            except Exception:
                pass
    for ekey in ("entities", "Entities"):
        if ekey in data and isinstance(data[ekey], dict):
            for dk in ("duration_minutes", "duration"):
                if dk in data[ekey] and data[ekey][dk] is not None:
                    try:
                        return int(data[ekey][dk])
                    except Exception:
                        pass
    return None


class AvailabilityAPI:
    """
    Availability API Layer for n8n.

    Provides availability checking with tolerant input handling.
    Always returns {available: bool, slots: [...], reason: str} with boolean.
    Handles:
    - JSON strings vs objects
    - $json.body / $json.data nesting
    - Business/Entities capitalized vs lowercase
    - separate date+time vs ISO start/scheduled_time
    - string booleans
    - tenant_id from business.tenant_id
    """

    def __init__(self, tenant_context: TenantContext | None = None):
        self.tenant_context = tenant_context or TenantContext()

    def check(self, payload: Any) -> dict:
        """
        Check availability. Accepts BookingRequest shape or AvailabilityRequest shape.
        Returns dict with boolean available - never string.
        """
        data = _extract_payload(payload)

        # Normalize capitalized keys to lowercase for BookingRequest
        # Build a normalized dict that BookingRequest.from_dict can understand
        normalized = dict(data)
        # If Entities capitalized exists, copy to entities
        if "Entities" in data and isinstance(data["Entities"], dict) and "entities" not in normalized:
            normalized["entities"] = data["Entities"]
        if "Business" in data and isinstance(data["Business"], dict) and "business" not in normalized:
            normalized["business"] = data["Business"]
        if "Customer" in data and isinstance(data["Customer"], dict) and "customer" not in normalized:
            normalized["customer"] = data["Customer"]

        # Resolve tenant_id with business fallback
        tenant_id = _resolve_tenant_id(data) or _resolve_tenant_id(normalized)
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        # Resolve service/date/time/duration for validation before building BookingRequest
        service = _resolve_service(data) or _resolve_service(normalized)
        pref_date = _resolve_date(data) or _resolve_date(normalized)
        pref_time = _resolve_time(data) or _resolve_time(normalized)
        duration = _resolve_duration(data) or _resolve_duration(normalized)

        # Inject resolved values into normalized for BookingRequest
        if service and not normalized.get("service"):
            normalized["service"] = service
        if pref_date and not normalized.get("preferred_date") and not normalized.get("date"):
            normalized["preferred_date"] = pref_date
        if pref_time and not normalized.get("preferred_time") and not normalized.get("time"):
            normalized["preferred_time"] = pref_time
        if duration and not normalized.get("duration_minutes"):
            normalized["duration_minutes"] = duration
        if tenant_id and not normalized.get("tenant_id"):
            normalized["tenant_id"] = tenant_id

        # Try to build BookingRequest from normalized
        try:
            request = BookingRequest.from_dict(normalized)
            # Override with resolved if BookingRequest missed capitalized
            if not request.service and service:
                request.service = service
            if not request.preferred_date and pref_date:
                request.preferred_date = pref_date
            if not request.preferred_time and pref_time:
                request.preferred_time = pref_time
            if not request.duration_minutes and duration:
                request.duration_minutes = duration
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
            available = any(s.available for s in slots) if slots else False
            return {
                "available": bool(available),
                "slots": [s.to_dict() for s in slots],
                "reason": "Slots provided" if slots else "No slots provided",
            }

        try:
            from heshly_core.services.booking.availability_checker import AvailabilityChecker
            from heshly_core.services.booking.staff_assignment import StaffMember

            staff_name = request.preferred_staff or data.get("staff") or normalized.get("staff") or "default"
            # also check Entities staff
            if not staff_name or staff_name == "default":
                for ekey in ("entities", "Entities"):
                    if ekey in data and isinstance(data[ekey], dict) and data[ekey].get("staff"):
                        staff_name = data[ekey].get("staff")
                        break
            staff = StaffMember(name=staff_name) if staff_name else None

            booked_slots = data.get("booked_slots") or data.get("bookedSlots") or data.get("events") or normalized.get("booked_slots") or []

            checker = AvailabilityChecker()
            available = checker.is_available(request, staff, booked_slots)

            slots = []
            if available:
                try:
                    date_str = str(request.preferred_date).split("T")[0]
                    time_str = str(request.preferred_time)
                    # normalize time to HH:MM:SS
                    if len(time_str.split(":")) == 2:
                        time_str = time_str + ":00"
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
