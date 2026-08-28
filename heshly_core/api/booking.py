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
    return value


def _extract_payload(payload: Any) -> dict:
    payload = _parse_json_if_string(payload)
    if isinstance(payload, dict):
        if "body" in payload and isinstance(payload["body"], dict):
            body = payload["body"]
            if any(k in body for k in ("customer_name", "customer_phone", "service", "start", "preferred_date")):
                return body
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("customer_name", "customer_phone", "service", "start")):
                return inner
        if "data" in payload and isinstance(payload["data"], dict):
            return payload["data"]
    if isinstance(payload, dict):
        return payload
    return {}


class BookingAPI:
    """
    Booking API Layer for n8n.

    Provides appointment booking with tolerant input handling.
    Always returns {success: bool, appointment_id, status, message} with boolean.
    Handles JSON strings, $json.body nesting, and separate date+time.
    """

    def __init__(self, tenant_context: TenantContext | None = None):
        self.tenant_context = tenant_context or TenantContext()

    def book(self, payload: Any) -> dict:
        """
        Book appointment. Accepts AppointmentRequest shape.
        Returns dict with boolean success - never string.
        """
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

        # Check conflicts
        try:
            from heshly_core.services.calendar.conflict_detector import ConflictDetector
            events = data.get("events") or data.get("booked_slots") or data.get("existing_events") or []
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

        # Check business hours
        try:
            from heshly_core.services.calendar.business_hours_manager import BusinessHoursManager
            hours = data.get("business_hours") or data.get("businessHours")
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

        # Create appointment - in real implementation would persist via ERPNext
        # For now, generate ID and return success
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
        appointment_id = data.get("appointment_id") or data.get("appointmentId") or data.get("id")
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
