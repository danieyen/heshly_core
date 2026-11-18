from __future__ import annotations

from typing import Any
from datetime import datetime, UTC, date

import frappe

from heshly_core.models.calendar import AvailabilityResult, CalendarProvider, TimeSlot
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

        # If caller explicitly supplied slots (e.g. legacy n8n path that already computed calendar events),
        # respect them. Otherwise we now query the live calendar provider (see below).
        # Back-compat: if slots are supplied, we still return them but this path is deprecated.
        if "slots" in data and isinstance(data["slots"], list) and len(data["slots"]) > 0:
            # Only short-circuit when slots were intentionally supplied with non-empty list.
            # Empty list must fall through to live calendar query.
            pass_slot_check = True
        else:
            pass_slot_check = False
        if pass_slot_check and "slots" in data and isinstance(data["slots"], list):
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

        # --- Live calendar availability (smallest targeted integration) ---
        # 1) Tenant already validated above (TenantContext). 2) Load persisted connection.
        # 3) Query the real provider for this tenant's calendar, then delegate overlap to AvailabilityEngine.
        try:
            return self._check_via_calendar_provider(request, data, normalized, service, duration)
        except Exception as e:
            # If calendar provider path raises, fall back to legacy checker ONLY when caller supplied booked_slots explicitly.
            # Otherwise fail closed (do not report available=true).
            booked_slots_fallback = data.get("booked_slots") or data.get("bookedSlots") or data.get("events") or normalized.get("booked_slots") or []
            if booked_slots_fallback:
                try:
                    from heshly_core.services.booking.availability_checker import AvailabilityChecker
                    from heshly_core.services.booking.staff_assignment import StaffMember
                    staff_name = request.preferred_staff or data.get("staff") or normalized.get("staff") or "default"
                    if not staff_name or staff_name == "default":
                        for ekey in ("entities", "Entities"):
                            if ekey in data and isinstance(data[ekey], dict) and data[ekey].get("staff"):
                                staff_name = data[ekey].get("staff")
                                break
                    staff = StaffMember(name=staff_name or "default", services=[service] if service else []) if staff_name else None
                    checker = AvailabilityChecker()
                    available = checker.is_available(request, staff, booked_slots_fallback)
                    slots = []
                    if available:
                        try:
                            date_str = str(request.preferred_date).split("T")[0]
                            time_str = str(request.preferred_time)
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
                        "reason": ("Slot is available" if available else "Slot conflicts with existing booking") + f" (fallback: {e})",
                    }
                except Exception:
                    pass
            return {
                "available": False,
                "slots": [],
                "reason": str(e) if str(e) else "Availability check failed",
            }

    def check_tolerant(self, payload: Any) -> dict:
        """Alias for check that handles all n8n wrapping."""
        return self.check(payload)

    def check_multi(self, payload: Any) -> dict:
        """
        Batch availability: handles candidate_times list.
        Input: {service, preferred_date, candidate_times: [HH:MM], timezone, tenant_id}
        Returns: {success, service, preferred_date, candidate_times, results: [{time, available, slots}], available: bool}
        """
        data = _extract_payload(payload)
        if "Entities" in data and isinstance(data["Entities"], dict) and "entities" not in data:
            data["entities"] = data["Entities"]
        if "Business" in data and isinstance(data["Business"], dict) and "business" not in data:
            data["business"] = data["Business"]

        candidate_times = _get_nested(data, "candidate_times", "candidateTimes", "times")
        if candidate_times is None:
            # also check entities.candidate_times
            for ekey in ("entities", "Entities"):
                if ekey in data and isinstance(data[ekey], dict):
                    candidate_times = data[ekey].get("candidate_times") or data[ekey].get("candidateTimes") or data[ekey].get("times")
                    if candidate_times:
                        break
        if isinstance(candidate_times, str):
            import json as _json
            try:
                candidate_times = _json.loads(candidate_times)
            except Exception:
                candidate_times = [candidate_times]
        if not isinstance(candidate_times, list):
            candidate_times = [candidate_times] if candidate_times else []
        # fallback to single preferred_time
        if not candidate_times:
            single = _resolve_time(data)
            if single:
                candidate_times = [single]
        if not candidate_times:
            return {"success": False, "reason": "candidate_times required", "available": False, "results": []}

        # normalize times to HH:MM
        norm_times: list[str] = []
        for t in candidate_times:
            if not t:
                continue
            s = str(t).strip()
            if len(s.split(":")) == 3:
                s = ":".join(s.split(":")[:2])
            if " " in s:
                # handle "6 am" already converted? but just in case
                pt = _resolve_time({"preferred_time": s})
                s = pt or s
            norm_times.append(s)
        candidate_times = norm_times

        service = _resolve_service(data)
        if not service:
            return {"success": False, "reason": "service is required", "available": False, "results": []}
        pref_date = _resolve_date(data)
        if not pref_date:
            return {"success": False, "reason": "preferred_date is required", "available": False, "results": []}
        duration = _resolve_duration(data) or 30

        tenant_id = _resolve_tenant_id(data)
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        results: list[dict] = []
        any_available = False
        for tm in candidate_times:
            single_payload = {
                "service": service,
                "preferred_date": pref_date,
                "preferred_time": tm,
                "duration_minutes": duration,
                "tenant_id": tenant_id or data.get("tenant_id"),
                "business": data.get("business") or data.get("Business") or {},
            }
            res = self.check(single_payload)
            avail = bool(res.get("available"))
            if avail:
                any_available = True
            results.append({
                "time": tm,
                "available": avail,
                "slots": res.get("slots", []),
                "reason": res.get("reason", ""),
            })

        return {
            "success": True,
            "service": service,
            "preferred_date": pref_date,
            "candidate_times": candidate_times,
            "available": any_available,
            "results": results,
        }

    @staticmethod
    def _check_multi_static(payload: Any) -> dict:
        return AvailabilityAPI().check_multi(payload)

    # ------------------------------------------------------------------
    # Live calendar integration
    # ------------------------------------------------------------------
    def _check_via_calendar_provider(
        self,
        request,  # BookingRequest
        data: dict,
        normalized: dict,
        service: str,
        duration: int | None,
    ) -> dict:
        # Validate tenant context exists (already set above). Fail closed if not.
        try:
            tenant_id = self.tenant_context.require()
        except Exception:
            # Also try to resolve from data once more for guest/n8n
            tid = _resolve_tenant_id(data) or _resolve_tenant_id(normalized)
            if tid:
                try:
                    self.tenant_context.set(tid)
                    tenant_id = self.tenant_context.require()
                except Exception as e:
                    return {"available": False, "slots": [], "reason": f"Missing tenant context: {e}"}
            else:
                return {"available": False, "slots": [], "reason": "Missing tenant context: tenant_id is required"}

        # Resolve requested start datetime in the tenant/calendar timezone
        # Use calendar connection timezone when available, else Business Account timezone, else UTC.
        try:
            date_str = str(request.preferred_date).split("T")[0]
            time_str = str(request.preferred_time).strip()
            if len(time_str.split(":")) == 2:
                time_str = time_str + ":00"
            # Build timezone handling: prefer calendar connection tz
            from datetime import timedelta
            import zoneinfo

            connection_tz_name = None
            connection = None
            try:
                from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository

                repo = CalendarConnectionRepository()
                # Prefer Google connection for now, but try any provider
                # List tenant connections (tenant-scoped)
                conns = repo.list(tenant_id=tenant_id)
                if conns:
                    # Prefer active Google, else first active, else first
                    for c in conns:
                        if getattr(c, "provider", None) == CalendarProvider.GOOGLE and getattr(c, "status", None) and str(getattr(c.status, "value", c.status)) == "active":
                            connection = c
                            break
                    if connection is None:
                        for c in conns:
                            if str(getattr(c.status, "value", c.status)) == "active":
                                connection = c
                                break
                    if connection is None:
                        connection = conns[0]
                    connection_tz_name = getattr(connection, "timezone", None) or getattr(connection, "timezone", "Africa/Nairobi")
                else:
                    connection = None
            except PermissionError as e:
                # Tenant isolation violation — never leak other tenant's connection
                return {"available": False, "slots": [], "reason": str(e)[:300]}
            except Exception:
                connection = None

            if connection is None:
                return {"available": False, "slots": [], "reason": "No calendar is connected for this tenant. Please connect Google Calendar first."}

            # Resolve timezone: connection tz → fallback Africa/Nairobi
            tz_name = (connection_tz_name or "Africa/Nairobi").strip() or "Africa/Nairobi"
            try:
                tz = zoneinfo.ZoneInfo(tz_name)
            except Exception:
                tz = zoneinfo.ZoneInfo("Africa/Nairobi")
                tz_name = "Africa/Nairobi"

            # Build requested start in that tz
            naive_start = datetime.fromisoformat(f"{date_str}T{time_str}")
            # Attach tz
            requested_start = naive_start.replace(tzinfo=tz)
            duration_min = int(request.duration_minutes or duration or 30)
            requested_end = requested_start + timedelta(minutes=duration_min)

            # Also handle legacy caller that supplied booked_slots/events explicitly:
            # merge those with live Google events (so explicit slots still matter).
            explicit_events: list = []
            # booked_slots/events in payload may be BookedSlot-like dicts, but AvailabilityEngine expects CalendarEvent.
            # We convert explicit booked_slots to CalendarEvent for unified overlap check.
            for key in ("booked_slots", "bookedSlots", "events"):
                maybe = data.get(key) or normalized.get(key)
                if isinstance(maybe, list) and maybe:
                    for item in maybe:
                        if isinstance(item, dict):
                            # Try CalendarEvent shape
                            if "start" in item:
                                try:
                                    s = item.get("start")
                                    e = item.get("end")
                                    if isinstance(s, str):
                                        s = datetime.fromisoformat(s.replace("Z", "+00:00"))
                                    if isinstance(e, str):
                                        e = datetime.fromisoformat(e.replace("Z", "+00:00"))
                                    if isinstance(s, datetime) and isinstance(e, datetime):
                                        from heshly_core.models.calendar import CalendarEvent as CE
                                        explicit_events.append(CE(event_id=item.get("event_id") or item.get("id") or "explicit", title=item.get("title") or "Booked", start=s, end=e))
                                        continue
                                except Exception:
                                    pass
                            # BookedSlot shape
                            if "date" in item and "time" in item:
                                try:
                                    d = str(item["date"]).split("T")[0]
                                    t = str(item["time"]).strip()
                                    if len(t.split(":")) == 2:
                                        t = t + ":00"
                                    s = datetime.fromisoformat(f"{d}T{t}").replace(tzinfo=tz)
                                    dur = int(item.get("duration_minutes") or item.get("duration") or 30)
                                    e = s + timedelta(minutes=dur)
                                    from heshly_core.models.calendar import CalendarEvent as CE
                                    explicit_events.append(CE(event_id="explicit", title="BookedSlot", start=s, end=e))
                                except Exception:
                                    continue

            # Query live provider for this tenant/day window
            # Window: start of requested day 00:00 to end of day 23:59:59 in calendar tz
            day_start = datetime.combine(requested_start.date(), datetime.min.time()).replace(tzinfo=tz)
            day_end = datetime.combine(requested_start.date(), datetime.max.time()).replace(tzinfo=tz)

            # Use provider abstraction: instantiate GoogleCalendarProvider (or ERPNext etc) via provider type
            provider_tenant_id_before = self.tenant_context.get()
            from heshly_core.models.calendar_provider import ProviderEventQuery
            from heshly_core.services.calendar.providers.google_calendar_provider import GoogleCalendarProvider
            from heshly_core.services.calendar.providers.provider_factory import ProviderFactory

            # Ensure TenantContext is set for provider's get_valid_access_token
            # (already set). Create provider via factory for the connection's provider.
            try:
                factory = ProviderFactory()
                provider = factory.create(connection.provider)  # type: ignore
            except Exception:
                # Fallback to Google if factory doesn't support it yet
                provider = GoogleCalendarProvider()

            # Ensure provider resolves correct tenant: it reads TenantContext internally
            # Query live events
            query = ProviderEventQuery(start=day_start, end=day_end)
            result = provider.get_events(query)
            if not result.success:
                # Do not assume available on provider error
                return {"available": False, "slots": [], "reason": f"Calendar query failed: {result.message[:300]}"}

            live_events = list(result.events or [])

            # Normalize live event times to calendar tz for comparison (provider already returns UTC-aware)
            # AvailabilityEngine.is_available compares raw datetimes; ensure requested_start/end and event times are comparable.
            # Keep everything tz-aware; Google returns UTC-aware (+00:00) which compares correctly with tz-aware requested_start (tz).
            all_events = live_events + explicit_events

            # Use existing AvailabilityEngine for overlap
            from heshly_core.services.calendar.availability_engine import AvailabilityEngine

            engine = AvailabilityEngine()
            is_available = engine.is_available(requested_start, duration_min, all_events)

            slots: list[dict] = []
            if is_available:
                # Return the requested slot as available
                slots.append(TimeSlot(start=requested_start, end=requested_end, available=True).to_dict())
                reason = "Slot is available"
            else:
                # Find conflicting event for reason
                conflict = None
                for ev in all_events:
                    if requested_start < ev.end and requested_end > ev.start:
                        conflict = ev
                        break
                if conflict:
                    reason = f"Slot conflicts with existing event: {conflict.title}"
                else:
                    reason = "Slot conflicts with existing booking"

            # Optionally, business hours check: if outside hours, mark unavailable
            # Reuse BusinessHoursManager if caller supplied business_hours
            bh = data.get("business_hours") or data.get("businessHours") or normalized.get("business_hours")
            if bh:
                try:
                    from heshly_core.services.calendar.business_hours_manager import BusinessHoursManager
                    from heshly_core.models.calendar import AppointmentRequest as AR

                    ar = AR(
                        customer_name="",
                        customer_phone="",
                        service=service or "",
                        start=requested_start,
                        duration_minutes=duration_min,
                    )
                    bhm = BusinessHoursManager()
                    bh_result = bhm.is_within_hours(ar, bh)
                    if not bh_result.within_hours:
                        return {"available": False, "slots": [], "reason": bh_result.message}
                except Exception:
                    pass

            return {"available": bool(is_available), "slots": slots, "reason": reason}

        except PermissionError as e:
            return {"available": False, "slots": [], "reason": str(e)[:300]}
        except Exception as e:
            # Fail closed on unexpected error
            return {"available": False, "slots": [], "reason": f"Availability check failed: {str(e)[:300]}"}

    def health(self) -> dict:
        return {
            "api": "availability_api",
            "status": "healthy",
        }


_api = AvailabilityAPI()


@frappe.whitelist(allow_guest=True, methods=["POST", "GET"])
def check_availability(*args: Any, **kwargs: Any) -> dict:
    # frappe passes cmd + form_dict fields as kwargs; consolidate into payload dict
    payload = args[0] if args else None
    # Handle explicit payload/data kw
    if isinstance(kwargs.get("payload"), dict):
        payload = kwargs.pop("payload")
    elif isinstance(kwargs.get("data"), dict):
        payload = kwargs.pop("data")
    elif isinstance(kwargs.get("payload"), str) or isinstance(kwargs.get("data"), str):
        payload = kwargs.pop("payload", kwargs.pop("data", None))
    # Remaining kwargs are form fields (service, preferred_date, etc.) plus cmd
    form_fields = {k: v for k, v in kwargs.items() if k != "cmd"}
    if form_fields:
        if payload is None:
            payload = dict(form_fields)
        elif isinstance(payload, dict):
            for k, v in form_fields.items():
                if k not in payload or payload[k] in (None, ""):
                    payload[k] = v
    return _api.check(payload)


@frappe.whitelist(allow_guest=True, methods=["POST", "GET"])
def check_availability_multi(*args: Any, **kwargs: Any) -> dict:
    payload = args[0] if args else None
    if isinstance(kwargs.get("payload"), dict):
        payload = kwargs.pop("payload")
    elif isinstance(kwargs.get("data"), dict):
        payload = kwargs.pop("data")
    elif isinstance(kwargs.get("payload"), str) or isinstance(kwargs.get("data"), str):
        payload = kwargs.pop("payload", kwargs.pop("data", None))
    form_fields = {k: v for k, v in kwargs.items() if k != "cmd"}
    if form_fields:
        if payload is None:
            payload = dict(form_fields)
        elif isinstance(payload, dict):
            for k, v in form_fields.items():
                if k not in payload or payload[k] in (None, ""):
                    payload[k] = v
    return _api.check_multi(payload)


@frappe.whitelist(allow_guest=True, methods=["POST", "GET"])
def check(*args: Any, **kwargs: Any) -> dict:
    payload = args[0] if args else None
    if isinstance(kwargs.get("payload"), dict):
        payload = kwargs.pop("payload")
    elif isinstance(kwargs.get("data"), dict):
        payload = kwargs.pop("data")
    form_fields = {k: v for k, v in kwargs.items() if k != "cmd"}
    if form_fields:
        if payload is None:
            payload = dict(form_fields)
        elif isinstance(payload, dict):
            for k, v in form_fields.items():
                if k not in payload or payload[k] in (None, ""):
                    payload[k] = v
    return _api.check(payload)


@frappe.whitelist(allow_guest=True, methods=["POST", "GET"])
def check_tolerant(*args: Any, **kwargs: Any) -> dict:
    payload = args[0] if args else None
    if isinstance(kwargs.get("payload"), dict):
        payload = kwargs.pop("payload")
    elif isinstance(kwargs.get("data"), dict):
        payload = kwargs.pop("data")
    form_fields = {k: v for k, v in kwargs.items() if k != "cmd"}
    if form_fields:
        if payload is None:
            payload = dict(form_fields)
        elif isinstance(payload, dict):
            for k, v in form_fields.items():
                if k not in payload or payload[k] in (None, ""):
                    payload[k] = v
    return _api.check(payload)
