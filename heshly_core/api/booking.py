from __future__ import annotations

from typing import Any
from datetime import datetime, UTC

from heshly_core.models.calendar import AppointmentRequest, AppointmentResult, AppointmentStatus
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
        if "body" in payload and isinstance(payload["body"], dict):
            body = payload["body"]
            if any(k in body for k in ("customer_name", "customer_phone", "service", "start", "preferred_date", "Business", "Entities", "tenant_id")):
                return body
            if "data" in body and isinstance(body["data"], dict):
                return body["data"]
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("customer_name", "customer_phone", "service", "start", "Business", "Entities")):
                return inner
        if "data" in payload and isinstance(payload["data"], dict):
            inner = payload["data"]
            if any(k in inner for k in ("Business", "Entities", "business", "entities", "service", "customer_name", "tenant_id")):
                return inner
            return inner
        if any(k in payload for k in ("Business", "Entities")):
            return payload
    if isinstance(payload, dict):
        return payload
    return {}


def _resolve_tenant_id(data: dict) -> str | None:
    for k in ("tenant_id", "tenantId"):
        if k in data and isinstance(data[k], str) and data[k].strip():
            return data[k].strip()
    for bkey in ("business", "Business"):
        if bkey in data and isinstance(data[bkey], dict):
            b = data[bkey]
            for tk in ("tenant_id", "tenantId", "id", "business_id"):
                if tk in b and isinstance(b[tk], str) and b[tk].strip():
                    return b[tk].strip()
    return None


def _resolve_service(data: dict) -> str | None:
    for k in ("service", "Service"):
        if k in data and isinstance(data[k], str) and data[k].strip():
            return data[k].strip()
    for ekey in ("entities", "Entities"):
        if ekey in data and isinstance(data[ekey], dict):
            for sk in ("service", "Service"):
                if sk in data[ekey] and isinstance(data[ekey][sk], str) and data[ekey][sk].strip():
                    return data[ekey][sk].strip()
    return None


def _resolve_customer_field(data: dict, field: str) -> str | None:
    # field is "name" or "phone" or "email"
    for k in (f"customer_{field}", f"customer{field.capitalize()}", field):
        if k in data and isinstance(data[k], str) and data[k].strip():
            return data[k].strip()
    for ckey in ("customer", "Customer"):
        if ckey in data and isinstance(data[ckey], dict):
            c = data[ckey]
            for ck in (field, "name" if field == "name" else field, "phone" if field == "phone" else field):
                if ck in c and isinstance(c[ck], str) and c[ck].strip():
                    return c[ck].strip()
            # also handle full_name
            if field == "name" and "full_name" in c and isinstance(c["full_name"], str) and c["full_name"].strip():
                return c["full_name"].strip()
    for ekey in ("entities", "Entities"):
        if ekey in data and isinstance(data[ekey], dict):
            if field in data[ekey] and isinstance(data[ekey][field], str) and data[ekey][field].strip():
                return data[ekey][field].strip()
    return None


def _resolve_scheduled_time(data: dict) -> str | None:
    for k in ("scheduled_time", "scheduledTime", "start", "appointment_date", "date"):
        if k in data and data[k]:
            v = str(data[k]).strip()
            if v:
                return v
    for ekey in ("entities", "Entities"):
        if ekey in data and isinstance(data[ekey], dict):
            for sk in ("scheduled_time", "date", "preferred_date"):
                if sk in data[ekey] and data[ekey][sk]:
                    v = str(data[ekey][sk]).strip()
                    if v:
                        # if date only, combine with time
                        if "T" not in v:
                            # try to get time
                            t = None
                            for tk in ("preferred_time", "time"):
                                if tk in data[ekey] and data[ekey][tk]:
                                    t = str(data[ekey][tk]).strip()
                                    break
                            if t:
                                if len(t.split(":")) == 2:
                                    t = t + ":00"
                                return f"{v}T{t}"
                        return v
    # try preferred_date + preferred_time at top level
    pd = data.get("preferred_date") or data.get("date")
    pt = data.get("preferred_time") or data.get("time")
    if pd and pt:
        try:
            date_str = str(pd).split("T")[0]
            time_str = str(pt)
            if len(time_str.split(":")) == 2:
                time_str = time_str + ":00"
            return f"{date_str}T{time_str}"
        except Exception:
            pass
    # also check Entities
    for ekey in ("entities", "Entities"):
        if ekey in data and isinstance(data[ekey], dict):
            pd = data[ekey].get("preferred_date") or data[ekey].get("date")
            pt = data[ekey].get("preferred_time") or data[ekey].get("time")
            if pd and pt:
                try:
                    date_str = str(pd).split("T")[0]
                    time_str = str(pt)
                    if len(time_str.split(":")) == 2:
                        time_str = time_str + ":00"
                    return f"{date_str}T{time_str}"
                except Exception:
                    pass
    return None


class BookingAPI:
    """
    Booking API Layer for n8n.

    Provides appointment booking with tolerant input handling.
    Always returns {success: bool, appointment_id, status, message} with boolean.
    Handles JSON strings, $json.body/data nesting, Business/Entities capitalized, and separate date+time.
    """

    def __init__(self, tenant_context: TenantContext | None = None):
        self.tenant_context = tenant_context or TenantContext()

    def book(self, payload: Any) -> dict:
        """
        Book appointment. Accepts AppointmentRequest shape.
        Returns dict with boolean success - never string.
        """
        data = _extract_payload(payload)

        # Normalize capitalized
        normalized = dict(data)
        if "Entities" in data and isinstance(data["Entities"], dict) and "entities" not in normalized:
            normalized["entities"] = data["Entities"]
        if "Business" in data and isinstance(data["Business"], dict) and "business" not in normalized:
            normalized["business"] = data["Business"]
        if "Customer" in data and isinstance(data["Customer"], dict) and "customer" not in normalized:
            normalized["customer"] = data["Customer"]

        tenant_id = _resolve_tenant_id(data) or _resolve_tenant_id(normalized)
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass
            if not normalized.get("tenant_id"):
                normalized["tenant_id"] = tenant_id

        # Resolve service/customer/scheduled_time if missing
        service = _resolve_service(data) or _resolve_service(normalized)
        if service and not normalized.get("service"):
            normalized["service"] = service

        cust_name = _resolve_customer_field(data, "name") or _resolve_customer_field(normalized, "name")
        cust_phone = _resolve_customer_field(data, "phone") or _resolve_customer_field(normalized, "phone")
        if cust_name and not normalized.get("customer_name"):
            normalized["customer_name"] = cust_name
        if cust_phone and not normalized.get("customer_phone"):
            normalized["customer_phone"] = cust_phone
        # also handle customer_name/phone directly from Customer object
        if not normalized.get("customer_name") and "customer" in normalized and isinstance(normalized["customer"], dict):
            cn = normalized["customer"].get("name") or normalized["customer"].get("full_name")
            if cn:
                normalized["customer_name"] = cn
        if not normalized.get("customer_phone") and "customer" in normalized and isinstance(normalized["customer"], dict):
            cp = normalized["customer"].get("phone")
            if cp:
                normalized["customer_phone"] = cp

        sched = _resolve_scheduled_time(data) or _resolve_scheduled_time(normalized)
        if sched and not normalized.get("scheduled_time") and not normalized.get("start"):
            normalized["scheduled_time"] = sched
            normalized["start"] = sched

        # duration
        dur = None
        for k in ("duration_minutes", "duration"):
            if k in data and data[k] is not None:
                try:
                    dur = int(data[k])
                    break
                except Exception:
                    pass
        if dur is None:
            for ekey in ("entities", "Entities"):
                if ekey in data and isinstance(data[ekey], dict):
                    for dk in ("duration_minutes", "duration"):
                        if dk in data[ekey] and data[ekey][dk] is not None:
                            try:
                                dur = int(data[ekey][dk])
                                break
                            except Exception:
                                pass
        if dur is not None and not normalized.get("duration_minutes"):
            normalized["duration_minutes"] = dur

        # notes
        notes = None
        for k in ("notes", "Notes"):
            if k in data and data[k]:
                notes = data[k]
                break
        if not notes:
            for ekey in ("entities", "Entities"):
                if ekey in data and isinstance(data[ekey], dict) and data[ekey].get("notes"):
                    notes = data[ekey].get("notes")
                    break
        if notes and not normalized.get("notes"):
            normalized["notes"] = notes

        try:
            request = AppointmentRequest.from_dict(normalized)
        except Exception as e:
            return {
                "success": False,
                "appointment_id": None,
                "status": None,
                "message": f"Invalid request: {e}",
            }

        errors = request.validate()
        if errors:
            return {
                "success": False,
                "appointment_id": None,
                "status": None,
                "message": f"Validation failed: {', '.join(errors)}",
            }

        try:
            from heshly_core.services.calendar.conflict_detector import ConflictDetector
            events = data.get("events") or data.get("booked_slots") or data.get("existing_events") or normalized.get("events") or []
            detector = ConflictDetector()
            conflict = detector.detect(request, events)
            if conflict.has_conflict:
                return {
                    "success": False,
                    "appointment_id": None,
                    "status": None,
                    "message": conflict.message,
                }
        except Exception:
            pass

        try:
            from heshly_core.services.calendar.business_hours_manager import BusinessHoursManager
            hours = data.get("business_hours") or data.get("businessHours") or normalized.get("business_hours")
            if hours:
                manager = BusinessHoursManager()
                result = manager.is_within_hours(request, hours)
                if not result.within_hours:
                    return {
                        "success": False,
                        "appointment_id": None,
                        "status": None,
                        "message": result.message,
                    }
        except Exception:
            pass

        import uuid
        appointment_id = str(uuid.uuid4())

        result = AppointmentResult(
            success=True,
            appointment_id=appointment_id,
            status=AppointmentStatus.CONFIRMED,
            message="Appointment booked successfully",
        )
        return result.to_dict()

    def create(self, payload: Any) -> dict:
        return self.book(payload)

    def confirm(self, payload: Any) -> dict:
        return self.book(payload)

    def cancel(self, payload: Any) -> dict:
        data = _extract_payload(payload)
        appointment_id = data.get("appointment_id") or data.get("appointmentId") or data.get("id") or data.get("appointment_id")
        # also check nested
        if not appointment_id:
            for wrapper in ("data", "body", "json"):
                if wrapper in data and isinstance(data[wrapper], dict):
                    inner = data[wrapper]
                    appointment_id = inner.get("appointment_id") or inner.get("appointmentId") or inner.get("id")
                    if appointment_id:
                        break
        if not appointment_id:
            return {
                "success": False,
                "appointment_id": None,
                "status": None,
                "message": "appointment_id is required",
            }
        return {
            "success": True,
            "appointment_id": str(appointment_id),
            "status": AppointmentStatus.CANCELLED.value,
            "message": "Appointment cancelled",
        }

    def health(self) -> dict:
        return {
            "api": "booking_api",
            "status": "healthy",
        }
