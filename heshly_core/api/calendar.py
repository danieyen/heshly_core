from __future__ import annotations

from typing import Any
from datetime import datetime, UTC

from heshly_core.models.calendar import AppointmentRequest, AppointmentResult, AppointmentStatus, CalendarEvent
from heshly_core.services.calendar.conflict_detector import ConflictDetector
from heshly_core.services.calendar.business_hours_manager import BusinessHoursManager
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
            if any(k in body for k in ("customer_name", "service", "start", "events", "business_hours")):
                return body
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("customer_name", "service", "start")):
                return inner
        if "data" in payload and isinstance(payload["data"], dict):
            return payload["data"]
    if isinstance(payload, dict):
        return payload
    return {}


class CalendarAPI:
    """
    Calendar API Layer for n8n.

    Provides calendar operations with tolerant input handling.
    Always returns boolean values correctly.
    """

    def __init__(self, tenant_context: TenantContext | None = None):
        self.tenant_context = tenant_context or TenantContext()
        self.conflict_detector = ConflictDetector()
        self.hours_manager = BusinessHoursManager()

    def check_conflict(self, payload: Any) -> dict:
        data = _extract_payload(payload)
        tenant_id = data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        try:
            request = AppointmentRequest.from_dict(data)
        except Exception as e:
            return {
                "has_conflict": True,
                "message": f"Invalid request: {e}",
                "conflicting_event": None,
            }

        events = data.get("events") or data.get("existing_events") or data.get("booked_slots") or []
        result = self.conflict_detector.detect(request, events)
        return result.to_dict()

    def check_business_hours(self, payload: Any) -> dict:
        data = _extract_payload(payload)
        tenant_id = data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        try:
            request = AppointmentRequest.from_dict(data)
        except Exception as e:
            return {
                "within_hours": False,
                "message": f"Invalid request: {e}",
            }

        hours = data.get("business_hours") or data.get("businessHours") or data.get("hours")
        if not hours:
            return {
                "within_hours": True,
                "message": "No business hours configured",
            }

        result = self.hours_manager.is_within_hours(request, hours)
        return result.to_dict()

    def book(self, payload: Any) -> dict:
        """
        Book appointment via calendar. Delegates to BookingAPI logic.
        Returns {success: bool, appointment_id, status, message}
        """
        from heshly_core.api.booking import BookingAPI

        api = BookingAPI(tenant_context=self.tenant_context)
        return api.book(payload)

    def list_events(self, payload: Any) -> dict:
        data = _extract_payload(payload)
        tenant_id = data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        # In real implementation, would query ERPNext
        return {
            "success": True,
            "events": [],
            "message": "Events listed",
        }

    def health(self) -> dict:
        return {
            "api": "calendar_api",
            "status": "healthy",
        }
