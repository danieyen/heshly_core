from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    import frappe
except ImportError:  # pragma: no cover
    class _MockWhitelist:
        def __call__(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator
    class _MockFrappe:
        whitelist = _MockWhitelist()
        request = None
        local = None
    frappe = _MockFrappe()  # type: ignore

try:
    from heshly_core.services.tenant.tenant_context import TenantContext
except ImportError:
    TenantContext = None  # type: ignore


def _parse_json_string(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return value
        if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")):
            try:
                return json.loads(v)
            except Exception:
                return value
    return value


def _unwrap_payload(payload: Any, kwargs: dict) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(kwargs, dict):
        data.update(kwargs)
    if payload is not None:
        parsed = _parse_json_string(payload)
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                if k not in data:
                    data[k] = v
            if not data:
                data = dict(parsed)
        elif isinstance(parsed, str) and parsed.strip():
            try:
                inner = json.loads(parsed)
                if isinstance(inner, dict):
                    data.update(inner)
            except Exception:
                pass
    for _ in range(3):
        wrapped = None
        for key in ("$json", "json", "body", "data", "payload"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    wrapped = val
                    break
        if wrapped is not None:
            merged = dict(data)
            merged.pop("$json", None)
            merged.pop("json", None)
            merged.pop("body", None)
            merged.pop("data", None)
            merged.pop("payload", None)
            for k, v in wrapped.items():
                v = _parse_json_string(v)
                if isinstance(v, dict) and "__rl" in v and "value" in v:
                    v = str(v["value"]).strip()
                if k not in merged or merged[k] is None or merged[k] == "":
                    merged[k] = v
            data = merged
        else:
            break
    for k, v in list(data.items()):
        if isinstance(v, dict) and "__rl" in v and "value" in v:
            data[k] = str(v["value"]).strip()
            continue
        parsed = _parse_json_string(v)
        if isinstance(parsed, dict) and parsed != v:
            data[k] = parsed
    if not data:
        try:
            req = getattr(frappe, "request", None)
            if req is not None:
                raw = None
                if hasattr(req, "data"):
                    raw = req.data
                elif hasattr(req, "json"):
                    raw = req.json
                if raw:
                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode("utf-8", errors="ignore")
                    parsed = _parse_json_string(raw)
                    if isinstance(parsed, dict):
                        data.update(parsed)
                    elif isinstance(raw, dict):
                        data.update(raw)
                if hasattr(frappe, "local") and hasattr(frappe.local, "form_dict"):
                    fd = getattr(frappe.local, "form_dict", {})
                    if isinstance(fd, dict) and fd:
                        for k, v in fd.items():
                            if k not in data:
                                data[k] = v
        except Exception:
            pass
    return data


def _get_param(data: dict[str, Any], candidates: list[str]) -> Any | None:
    if not isinstance(data, dict) or not data:
        return None
    lower_map: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(k, str):
            lower_map[k.strip().lower()] = v
            lower_map[k.strip().lower().replace("_", "")] = v
            lower_map[k.strip().lower().replace("-", "")] = v
    for cand in candidates:
        if cand in data and data[cand] not in (None, ""):
            return data[cand]
        lc = cand.lower()
        if lc in lower_map and lower_map[lc] not in (None, ""):
            return lower_map[lc]
        lc_nounder = lc.replace("_", "")
        if lc_nounder in lower_map and lower_map[lc_nounder] not in (None, ""):
            return lower_map[lc_nounder]
        cap = cand.capitalize()
        if cap in data and data[cap] not in (None, ""):
            return data[cap]
        if cap.lower() in lower_map and lower_map[cap.lower()] not in (None, ""):
            return lower_map[cap.lower()]
    return None


class BookingAPI:
    """
    Booking API — production path uses persisted calendar provider via existing abstractions.

    Backward-compatible _store/_by_tenant kept for legacy list/get/cancel tests, but NEVER
    used to fabricate success for the production booking path.
    """

    def __init__(self, tenant_context: Any | None = None):
        self._store: dict[str, dict[str, Any]] = {}
        self._by_tenant: dict[str, list[dict[str, Any]]] = {}
        self._lock = threading.RLock()
        if tenant_context is not None:
            self._tenant_context = tenant_context
        elif TenantContext is not None:
            try:
                self._tenant_context = TenantContext()
            except Exception:
                self._tenant_context = None
        else:
            self._tenant_context = None

    def _get_tenant_context(self):
        if getattr(self, "_tenant_context", None) is not None:
            return self._tenant_context
        if TenantContext is not None:
            try:
                return TenantContext()
            except Exception:
                return None
        return None

    def _extract_tenant_id(self, data: dict[str, Any]) -> str | None:
        tenant_id = _get_param(data, ["tenant_id", "tenantId", "business_id", "businessId", "customer_tenant_id"])
        if tenant_id is not None:
            if isinstance(tenant_id, dict) and "value" in tenant_id:
                tenant_id = tenant_id["value"]
            tenant_id = str(tenant_id).strip()
            if tenant_id and tenant_id.lower() not in ("undefined", "null", "none", ""):
                # Canonical heshly studio tenant is valid — do not treat as missing.
                # Previous code returned None for heshly, breaking production bookings for that tenant.
                return tenant_id
        # Fallback to TenantContext when set via middleware/session
        if TenantContext is not None:
            try:
                ctx = TenantContext()
                val = ctx.get() if hasattr(ctx, "get") else None
                if isinstance(val, str) and val.strip():
                    return val.strip()
            except Exception:
                pass
        return None

    def _validate_membership(self, tenant_id: str) -> str | None:
        """Return error string if authenticated user has no membership for tenant, else None."""
        try:
            import frappe as _f
            _user = getattr(_f.session, "user", "Guest") if hasattr(_f, "session") else "Guest"
            if _user != "Guest" and _user:
                _has = _f.db.get_value("User Business Membership", {"user": _user, "tenant_id": tenant_id, "active": 1}, "name")
                if not _has:
                    return "tenant mismatch: no membership for requested tenant"
        except Exception:
            pass
        return None

    def _resolve_calendar_connection(self, tenant_id: str):
        """Load persisted tenant calendar connection (Heshly Calendar Connection)."""
        from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
        repo = CalendarConnectionRepository()
        conns = repo.list(tenant_id=tenant_id)
        if not conns:
            return None, repo
        # Prefer active, then any
        active = [c for c in conns if str(getattr(getattr(c, "status", ""), "value", c.status)) == "active"]
        chosen = active[0] if active else conns[0]
        # Also prefer provider priority? Keep chosen as is (Google for heshly today)
        return chosen, repo

    def _build_appointment_request(self, data: dict[str, Any], tenant_tz: str):
        """Build AppointmentRequest with correct timezone-aware start."""
        from heshly_core.models.calendar import AppointmentRequest
        # Use existing AppointmentRequest.from_dict where possible, but ensure correct tz handling
        # We need service, customer_name/phone, notes, start, duration, staff
        # Normalize start
        customer_name = str(_get_param(data, ["customer_name", "customerName", "name", "full_name"]) or _get_param(data.get("appointment", {}) if isinstance(data.get("appointment"), dict) else {}, ["customer_name"]) or _get_param(data, ["customer_id"]) or "Customer").strip() or "Customer"
        # More tolerant: try nested appointment block first
        appt_block = _get_param(data, ["appointment", "booking", "event"])
        if isinstance(appt_block, dict):
            if not customer_name or customer_name == "Customer":
                cn = _get_param(appt_block, ["customer_name", "customerName", "name"])
                if cn:
                    customer_name = str(cn).strip()
        phone = str(_get_param(data, ["phone_number", "phoneNumber", "phone", "mobile", "customer_phone", "customerPhone"]) or _get_param(appt_block if isinstance(appt_block, dict) else {}, ["phone_number", "phone"]) or "").strip()
        if not phone:
            # fallback to customer_id if it's a phone-like string
            cid = _get_param(data, ["customer_id", "customerId"])
            if cid and str(cid).strip().startswith("+"):
                phone = str(cid).strip()
        service = str(_get_param(data, ["service", "service_name", "serviceName", "treatment"]) or _get_param(appt_block if isinstance(appt_block, dict) else {}, ["service"]) or "").strip()
        if not service:
            service = "Consultation"
        notes = _get_param(data, ["notes", "note", "message", "description", "remarks"])
        if isinstance(notes, dict):
            notes = None
        notes = str(notes).strip() if notes else None

        # Extract date/time/start
        date = _get_param(data, ["date", "appointment_date", "appointmentDate", "booking_date", "bookingDate", "preferred_date"])
        time = _get_param(data, ["time", "appointment_time", "appointmentTime", "slot", "start_time", "startTime", "preferred_time"])
        start_raw = _get_param(data, ["start", "start_at", "startAt", "datetime", "appointment_datetime", "scheduled_time"])
        if isinstance(appt_block, dict):
            if not date:
                date = _get_param(appt_block, ["date", "appointment_date", "preferred_date"])
            if not time:
                time = _get_param(appt_block, ["time", "appointment_time", "preferred_time"])
            if not start_raw:
                start_raw = _get_param(appt_block, ["start", "start_at", "datetime", "scheduled_time"])
        if start_raw and not date:
            try:
                s = str(start_raw).strip()
                if "T" in s:
                    date = s.split("T")[0]
                    if not time:
                        time = s.split("T")[1].split(".")[0].split("Z")[0].split("+")[0][:5]
                else:
                    date = s
            except Exception:
                pass

        # Resolve duration
        duration = _get_param(data, ["duration_minutes", "duration", "durationMinutes"])
        if duration is None and isinstance(appt_block, dict):
            duration = _get_param(appt_block, ["duration_minutes", "duration"])
        try:
            duration_minutes = int(duration) if duration is not None else 30
        except Exception:
            duration_minutes = 30

        # Build start datetime with correct tz
        import zoneinfo
        start_dt = None
        if start_raw:
            s = str(start_raw).strip()
            # If ISO with explicit offset, respect it
            try:
                # Handle Z
                iso = s.replace("Z", "+00:00")
                # If contains offset or T, parse directly
                if "T" in iso:
                    # If has offset, fromisoformat will keep tz
                    dt = datetime.fromisoformat(iso)
                    if dt.tzinfo is None:
                        # No offset → interpret in tenant tz
                        try:
                            tz = zoneinfo.ZoneInfo(tenant_tz)
                        except Exception:
                            tz = zoneinfo.ZoneInfo("Africa/Nairobi")
                        dt = dt.replace(tzinfo=tz)
                    start_dt = dt
                elif " " in s and ":" in s:
                    # "2026-09-08 10:00" form
                    try:
                        dt = datetime.fromisoformat(s.replace(" ", "T"))
                    except Exception:
                        dt = None
                    if dt is not None and dt.tzinfo is None:
                        try:
                            tz = zoneinfo.ZoneInfo(tenant_tz)
                        except Exception:
                            tz = zoneinfo.ZoneInfo("Africa/Nairobi")
                        dt = dt.replace(tzinfo=tz)
                    start_dt = dt
            except Exception:
                pass
        if start_dt is None and date and time:
            try:
                ts = str(time).strip()
                if len(ts.split(":")) == 2:
                    ts = ts + ":00"
                naive = datetime.fromisoformat(f"{str(date).strip()}T{ts}")
                try:
                    tz = zoneinfo.ZoneInfo(tenant_tz)
                except Exception:
                    tz = zoneinfo.ZoneInfo("Africa/Nairobi")
                start_dt = naive.replace(tzinfo=tz)
            except Exception:
                pass
        if start_dt is None and date:
            # Date only → 00:00
            try:
                naive = datetime.fromisoformat(f"{str(date).strip()}T00:00:00")
                try:
                    tz = zoneinfo.ZoneInfo(tenant_tz)
                except Exception:
                    tz = zoneinfo.ZoneInfo("Africa/Nairobi")
                start_dt = naive.replace(tzinfo=tz)
            except Exception:
                pass

        if start_dt is None:
            return None, "start datetime could not be determined from payload (need date+time or start)"

        if not customer_name or customer_name.lower() == "guest":
            # Try lead/customer block
            cn2 = _get_param(data, ["customer_name"])
            if cn2 and str(cn2).strip():
                customer_name = str(cn2).strip()
            else:
                customer_name = "Customer"

        req = AppointmentRequest(
            customer_name=str(customer_name).strip() or "Customer",
            customer_phone=str(phone).strip() or "",
            service=str(service).strip() or "Consultation",
            start=start_dt,
            duration_minutes=duration_minutes,
            notes=notes,
        )
        return req, None

    def book_appointment(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        data = _unwrap_payload(payload, kwargs)
        tenant_id = self._extract_tenant_id(data)
        if not tenant_id:
            return {"success": False, "error": "tenant_id is required", "tenant_id": None}
        # Membership guard
        err = self._validate_membership(tenant_id)
        if err:
            return {"success": False, "error": err, "tenant_id": None}

        # Establish TenantContext for downstream provider resolution
        try:
            if TenantContext is not None:
                TenantContext().set(tenant_id)
        except Exception:
            pass

        # Load persisted connection (fail closed if none)
        try:
            connection, _repo = self._resolve_calendar_connection(tenant_id)
        except PermissionError as e:
            return {"success": False, "error": str(e), "tenant_id": tenant_id}
        except Exception as e:
            return {"success": False, "error": f"calendar connection lookup failed: {e}", "tenant_id": tenant_id}

        if connection is None:
            return {"success": False, "error": "No active calendar connection configured for this tenant", "tenant_id": tenant_id}

        # Build appointment request in tenant tz
        tenant_tz = getattr(connection, "timezone", None) or "Africa/Nairobi"
        req, err_msg = self._build_appointment_request(data, tenant_tz)
        if req is None:
            return {"success": False, "error": err_msg or "invalid appointment request", "tenant_id": tenant_id}

        # Validation via model
        try:
            errs = req.validate() if hasattr(req, "validate") else []
            if errs:
                return {"success": False, "error": "; ".join(errs), "tenant_id": tenant_id}
        except Exception:
            pass

        # Re-check availability immediately before booking (race protection)
        try:
            from heshly_core.models.calendar_provider import ProviderEventQuery
            from heshly_core.services.calendar.providers.provider_factory import ProviderFactory
            from heshly_core.services.calendar.availability_engine import AvailabilityEngine

            # Query window: exact appointment window (with small padding)
            start = req.start
            end = start + timedelta(minutes=req.duration_minutes)
            # Query with padding to catch edge overlaps
            q_start = start - timedelta(minutes=1)
            q_end = end + timedelta(minutes=1)
            query = ProviderEventQuery(start=q_start, end=q_end)
            factory = ProviderFactory()
            try:
                provider = factory.create(connection.provider)
            except Exception:
                from heshly_core.services.calendar.providers.google_calendar_provider import GoogleCalendarProvider
                provider = GoogleCalendarProvider()
            # Provider reads TenantContext internally for token resolution
            result = provider.get_events(query)
            if not result.success:
                return {"success": False, "error": f"Calendar query failed: {result.message[:300]}", "tenant_id": tenant_id}
            engine = AvailabilityEngine()
            available = engine.is_available(start, req.duration_minutes, list(result.events or []))
            if not available:
                return {"success": False, "error": "The requested appointment time is no longer available", "tenant_id": tenant_id}
        except PermissionError as e:
            return {"success": False, "error": str(e)[:300], "tenant_id": tenant_id}
        except Exception as e:
            return {"success": False, "error": f"Availability re-check failed: {str(e)[:300]}", "tenant_id": tenant_id}

        # Proceed via AppointmentManager (canonical path) — this calls ProviderIntegration.create_event
        try:
            from heshly_core.services.calendar.appointment_manager import AppointmentManager
            from heshly_core.services.calendar.providers.provider_integration import ProviderIntegration
            from heshly_core.models.calendar_provider import ProviderConnection
            from heshly_core.models.calendar import CalendarConfiguration

            # Build ProviderConnection for AppointmentManager's ProviderIntegration
            # The provider implementation (Google) will actually resolve tokens via repository + TenantContext,
            # so the ProviderConnection's tokens can be None; config must be correct.
            # Keep display business_name as connection's business_name if any.
            cfg = CalendarConfiguration(
                provider=connection.provider,
                calendar_id=connection.calendar_id,
                timezone=connection.timezone or tenant_tz,
                tenant_id=connection.tenant_id,
                business_name=getattr(connection, "business_name", "") or "",
            )
            provider_conn = ProviderConnection(
                configuration=cfg,
                access_token=getattr(connection, "access_token", None),
                refresh_token=getattr(connection, "refresh_token", None),
                expires_at=getattr(connection, "expires_at", None),
            )
            provider_integration = ProviderIntegration()
            try:
                provider_integration.connect(provider_conn)
            except Exception:
                pass
            manager = AppointmentManager(provider=provider_integration)
            appt_result = manager.create(req)
            if not appt_result.success:
                return {"success": False, "error": appt_result.message or "Provider booking failed", "tenant_id": tenant_id, "provider": connection.provider.value if hasattr(connection.provider, "value") else str(connection.provider)}
            real_id = appt_result.appointment_id
            # Optionally, create an ERPNext Appointment CRM record AFTER provider success (best-effort, not blocking)
            erp_name = None
            try:
                import frappe
                from datetime import datetime as _dt
                # Reuse existing tenant Lead to avoid duplicate Lead via Appointment.link_customer_lead
                _party = None
                _appt_with = None
                try:
                    from heshly_core.services.tenant.tenant_context import TenantContext

                    TenantContext().set(tenant_id)
                    from heshly_core.repositories.repository_factory import repository_factory

                    repo = repository_factory.leads
                    existing_lead = None
                    # Try phone first (canonical), then email
                    if req.customer_phone:
                        try:
                            existing_lead = repo.find_by_phone(req.customer_phone)
                        except Exception:
                            existing_lead = None
                    if not existing_lead and req.customer_phone:
                        # try normalized digits match
                        try:
                            rows = repo.search(req.customer_phone)
                            for r in rows:
                                if r.phone and req.customer_phone and r.phone.replace(" ", "") in req.customer_phone.replace(" ", ""):
                                    existing_lead = r
                                    break
                        except Exception:
                            pass
                    if existing_lead:
                        _party = frappe.db.get_value(
                            "Lead",
                            {"custom_heshly_lead_id": existing_lead.lead_id, "custom_heshly_tenant_id": tenant_id},
                            "name",
                        ) or frappe.db.get_value(
                            "Lead",
                            {"mobile_no": existing_lead.phone, "custom_heshly_tenant_id": tenant_id},
                            "name",
                        )
                        if _party:
                            _appt_with = "Lead"
                    # Also mark Lead as Converted on booking (ERPNext semantics)
                    if _party and existing_lead:
                        try:
                            from heshly_core.models.crm import LeadStatus

                            if existing_lead.status != LeadStatus.CONVERTED:
                                from heshly_core.services.crm.lead_status_manager import LeadStatusManager

                                # Allow QUALIFIED -> CONVERTED
                                try:
                                    LeadStatusManager().change_status(existing_lead, LeadStatus.CONVERTED)
                                except Exception:
                                    existing_lead.status = LeadStatus.CONVERTED
                                repo.save(existing_lead)
                        except Exception:
                            pass
                except Exception:
                    pass
                # ERPNext Appointment is CRM/reporting only; do not fail the booking if this fails
                _lead_email = ""
                try:
                    if _party:
                        _lead_email = frappe.db.get_value("Lead", _party, "email_id") or ""
                except Exception:
                    pass
                # ERPNext Appointment expects naive datetime in site tz; req.start is tz-aware (tenant tz)
                _scheduled_naive = req.start
                try:
                    import zoneinfo as _zi

                    _site_tz = frappe.db.get_single_value("System Settings", "time_zone") or "Africa/Nairobi"
                    _site_zone = _zi.ZoneInfo(_site_tz)
                    if _scheduled_naive.tzinfo is not None:
                        _scheduled_naive = _scheduled_naive.astimezone(_site_zone).replace(tzinfo=None)
                except Exception:
                    if _scheduled_naive.tzinfo is not None:
                        _scheduled_naive = _scheduled_naive.replace(tzinfo=None)
                _doc_kwargs = {
                    "doctype": "Appointment",
                    "scheduled_time": _scheduled_naive,
                    "status": "Open",
                    "customer_name": req.customer_name[:140] if req.customer_name else "WhatsApp Customer",
                    "customer_phone_number": req.customer_phone[:20] if req.customer_phone else "",
                    "customer_email": _lead_email or "noreply@heshly.com",
                    "custom_heshly_tenant_id": tenant_id,
                }
                if _party:
                    _doc_kwargs["party"] = _party
                    _doc_kwargs["appointment_with"] = _appt_with or "Lead"
                # Set flag so Event->Communication hooks propagate tenant
                frappe.flags.custom_heshly_tenant_id = tenant_id
                try:
                    from heshly_core.services.tenant.tenant_context import TenantContext

                    TenantContext().set(tenant_id)
                except Exception:
                    pass
                doc = frappe.get_doc(_doc_kwargs)
                doc.insert(ignore_permissions=True)
                try:
                    frappe.db.commit()
                except Exception:
                    pass
                erp_name = doc.name
            except Exception:
                pass
            # Maintain legacy in-memory store for list/get/cancel compatibility, but only on real success
            appointment = {
                "appointment_id": real_id,
                "tenant_id": tenant_id,
                "customer_id": req.customer_name,
                "phone_number": req.customer_phone,
                "service": req.service,
                "start": req.start.isoformat(),
                "end": (req.start + timedelta(minutes=req.duration_minutes)).isoformat(),
                "notes": req.notes,
                "status": appt_result.status.value if hasattr(appt_result.status, "value") else (appt_result.status or "confirmed"),
                "calendar_event_id": real_id,
                "erp_appointment": erp_name,
                "provider": connection.provider.value if hasattr(connection.provider, "value") else str(connection.provider),
            }
            with self._lock:
                self._store[real_id] = appointment
                self._by_tenant.setdefault(tenant_id, []).append(appointment)
            # Canonical response shape
            return {
                "success": True,
                "appointment_id": real_id,
                "provider": connection.provider.value if hasattr(connection.provider, "value") else str(connection.provider),
                "status": appt_result.status.value if hasattr(appt_result.status, "value") else (appt_result.status or "confirmed"),
                "message": appt_result.message or "Appointment booked successfully",
                "tenant_id": tenant_id,
                "appointment": appointment,
            }
        except Exception as e:
            return {"success": False, "error": f"Booking failed: {str(e)[:300]}", "tenant_id": tenant_id, "provider": connection.provider.value if hasattr(connection, "provider") and hasattr(connection.provider, "value") else None}

    def book(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        """Canonical alias for CalendarAPI compatibility."""
        return self.book_appointment(payload, **kwargs)

    def get(self, payload: Any = None, **kwargs: Any) -> dict[str, Any] | None:
        try:
            data = _unwrap_payload(payload, kwargs)
            appointment_id = _get_param(data, ["appointment_id", "appointmentId", "id", "booking_id", "bookingId"])
            tenant_id = self._extract_tenant_id(data)
            if not appointment_id:
                return None
            appointment_id = str(appointment_id).strip()
            with self._lock:
                appt = self._store.get(appointment_id)
                if appt is None:
                    return None
                if tenant_id and appt.get("tenant_id") != tenant_id:
                    return None
                return dict(appt)
        except Exception:
            return None

    def list(self, payload: Any = None, **kwargs: Any) -> list[dict[str, Any]]:
        try:
            data = _unwrap_payload(payload, kwargs)
            tenant_id = self._extract_tenant_id(data)
            if not tenant_id:
                return []
            with self._lock:
                return [dict(a) for a in self._by_tenant.get(tenant_id, [])]
        except Exception:
            return []

    def cancel(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        try:
            data = _unwrap_payload(payload, kwargs)
            appointment_id = _get_param(data, ["appointment_id", "appointmentId", "id", "booking_id"])
            tenant_id = self._extract_tenant_id(data)
            if not tenant_id:
                return {"success": False, "error": "tenant_id is required"}
            if not appointment_id:
                return {"success": False, "error": "appointment_id is required"}
            appointment_id = str(appointment_id).strip()
            # Prefer provider-backed cancel when we have a connection
            try:
                from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
                from heshly_core.services.calendar.appointment_manager import AppointmentManager
                from heshly_core.services.calendar.providers.provider_integration import ProviderIntegration
                from heshly_core.models.calendar_provider import ProviderConnection
                from heshly_core.models.calendar import CalendarConfiguration
                if TenantContext is not None:
                    try:
                        TenantContext().set(tenant_id)
                    except Exception:
                        pass
                repo = CalendarConnectionRepository()
                conns = repo.list(tenant_id=tenant_id)
                if conns:
                    # Prefer active/google
                    chosen = None
                    for c in conns:
                        if str(getattr(getattr(c, "status", ""), "value", c.status)) == "active":
                            chosen = c
                            break
                    chosen = chosen or conns[0]
                    cfg = CalendarConfiguration(provider=chosen.provider, calendar_id=chosen.calendar_id, timezone=chosen.timezone or "Africa/Nairobi", tenant_id=chosen.tenant_id, business_name=getattr(chosen, "business_name", "") or "")
                    pc = ProviderConnection(configuration=cfg, access_token=getattr(chosen, "access_token", None), refresh_token=getattr(chosen, "refresh_token", None), expires_at=getattr(chosen, "expires_at", None))
                    pi = ProviderIntegration()
                    try:
                        pi.connect(pc)
                    except Exception:
                        pass
                    mgr = AppointmentManager(provider=pi)
                    res = mgr.cancel(appointment_id)
                    if res.success:
                        with self._lock:
                            appt = self._store.get(appointment_id)
                            if appt and appt.get("tenant_id") == tenant_id:
                                appt["status"] = "cancelled"
                                appt["updated_at"] = datetime.now(UTC).isoformat()
                                return {"success": True, "appointment_id": appointment_id, "appointment": dict(appt)}
                        return {"success": True, "appointment_id": appointment_id}
                    else:
                        return {"success": False, "error": res.message or "Cancel failed"}
            except Exception:
                pass
            with self._lock:
                appt = self._store.get(appointment_id)
                if appt is None:
                    return {"success": False, "error": "appointment not found"}
                if tenant_id and appt.get("tenant_id") != tenant_id:
                    return {"success": False, "error": "tenant mismatch"}
                appt["status"] = "cancelled"
                appt["updated_at"] = datetime.now(UTC).isoformat()
                return {"success": True, "appointment_id": appointment_id, "appointment": dict(appt)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def health(self) -> dict[str, Any]:
        return {"service": "booking_api", "status": "healthy"}

_api = BookingAPI()

@frappe.whitelist(allow_guest=True)
def book_appointment(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = args[0] if args else None
    if payload is None and "payload" in kwargs:
        payload = kwargs.pop("payload")
    if payload is None and "data" in kwargs and isinstance(kwargs["data"], (dict, str)):
        payload = kwargs.get("data")
    return _api.book_appointment(payload, **kwargs)

@frappe.whitelist(allow_guest=True)
def create_appointment(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return book_appointment(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def create(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return book_appointment(*args, **kwargs)

# Back-compat alias for CalendarAPI.book() → BookingAPI.book()
@frappe.whitelist(allow_guest=True)
def book(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return book_appointment(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def get(*args: Any, **kwargs: Any) -> dict[str, Any] | None:
    payload = args[0] if args else None
    return _api.get(payload, **kwargs)

@frappe.whitelist(allow_guest=True)
def list_appointments(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    payload = args[0] if args else None
    return _api.list(payload, **kwargs)

@frappe.whitelist(allow_guest=True)
def cancel_appointment(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = args[0] if args else None
    if payload is None and "payload" in kwargs:
        payload = kwargs.pop("payload")
    return _api.cancel(payload, **kwargs)

@frappe.whitelist(allow_guest=True)
def health(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _api.health()
