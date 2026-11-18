"""Propagate Heshly tenant from Appointment -> Event -> Communication.

ERPNext's Event.sync_communication creates Communication without Heshly tenant.
This hook infers tenant from the Event's linked Appointment (or Lead) and sets
Communication.custom_heshly_tenant_id before validation, keeping reqd=1 safe.
"""
from __future__ import annotations

import frappe


def _infer_tenant_from_reference(reference_doctype: str | None, reference_name: str | None) -> str | None:
    if not reference_doctype or not reference_name:
        return None
    try:
        if reference_doctype == "Appointment":
            return frappe.db.get_value("Appointment", reference_name, "custom_heshly_tenant_id")
        if reference_doctype == "Lead":
            return frappe.db.get_value("Lead", reference_name, "custom_heshly_tenant_id")
        if reference_doctype == "Event":
            return frappe.db.get_value("Event", reference_name, "custom_heshly_tenant_id")
    except Exception:
        return None
    return None


def communication_before_insert(doc, method=None):
    """Set custom_heshly_tenant_id if missing by inferring from reference or Event.

    Order:
    1. Already set -> keep.
    2. frappe.flags.custom_heshly_tenant_id (set by BookingAPI).
    3. TenantContext (simulator / n8n).
    4. Reference Doctype (Appointment/Lead) linked directly.
    5. Event that triggered this Communication (via communication.reference_doctype == 'Event' or EventParticipants).
    6. Do not fail — leave None and let mandatory handle non-Heshly communications.
    """
    try:
        current = getattr(doc, "custom_heshly_tenant_id", None)
        if current and str(current).strip():
            return

        # 2. Flag set by booking path
        flag = getattr(frappe.flags, "custom_heshly_tenant_id", None)
        if flag and str(flag).strip():
            doc.custom_heshly_tenant_id = str(flag).strip()
            return

        # 3. TenantContext
        try:
            from heshly_core.services.tenant.tenant_context import TenantContext

            ctx = TenantContext().get()
            if ctx and str(ctx).strip():
                doc.custom_heshly_tenant_id = str(ctx).strip()
                return
        except Exception:
            pass

        # 4. Direct reference (Appointment/Lead) via Communication Link or fields
        ref_doctype = getattr(doc, "reference_doctype", None)
        ref_name = getattr(doc, "reference_name", None)
        tenant = _infer_tenant_from_reference(ref_doctype, ref_name)
        if tenant and str(tenant).strip():
            doc.custom_heshly_tenant_id = str(tenant).strip()
            return

        # Try Communication Link child
        try:
            links = getattr(doc, "timeline_links", None) or getattr(doc, "communication_link", None) or []
            # Frappe Communication uses `communication_link` for child table? Check both
            for link in getattr(doc, "links", []) or []:
                try:
                    lt = getattr(link, "link_doctype", None) or link.get("link_doctype")
                    ln = getattr(link, "link_name", None) or link.get("link_name")
                    t = _infer_tenant_from_reference(lt, ln)
                    if t and str(t).strip():
                        doc.custom_heshly_tenant_id = str(t).strip()
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # 5. Event that created this Communication: Communication.reference_doctype == 'Event' -> Event.custom_heshly_tenant_id or its Appointment
        if ref_doctype == "Event" and ref_name:
            event_tenant = frappe.db.get_value("Event", ref_name, "custom_heshly_tenant_id")
            if event_tenant and str(event_tenant).strip():
                doc.custom_heshly_tenant_id = str(event_tenant).strip()
                return
            # Fall back to Appointment linked to this Event
            try:
                appt = frappe.db.get_value("Appointment", {"calendar_event": ref_name}, "custom_heshly_tenant_id")
                if appt and str(appt).strip():
                    doc.custom_heshly_tenant_id = str(appt).strip()
                    return
                # Also try Event.participants -> Appointment party
                # Try to resolve via Event participants -> Lead
                participants = frappe.db.get_all(
                    "Event Participants",
                    filters={"parent": ref_name},
                    fields=["reference_doctype", "reference_docname"],
                    limit=5,
                )
                for p in participants:
                    t = _infer_tenant_from_reference(p["reference_doctype"], p["reference_docname"])
                    if t and str(t).strip():
                        doc.custom_heshly_tenant_id = str(t).strip()
                        return
            except Exception:
                pass

        # For Heshly Appointments, tenant is required. For non-Heshly communications, allow empty (reqd=0 will be updated to 1 only for Heshly docs via validation below).
        # So we don't throw here.
    except Exception:
        pass


def event_before_insert(doc, method=None):
    """Propagate tenant from Appointment to Event if Appointment created the Event."""
    try:
        if getattr(doc, "custom_heshly_tenant_id", None) and str(doc.custom_heshly_tenant_id).strip():
            return
        # 2. Flag
        flag = getattr(frappe.flags, "custom_heshly_tenant_id", None)
        if flag and str(flag).strip():
            doc.custom_heshly_tenant_id = str(flag).strip()
            return
        # 3. TenantContext
        try:
            from heshly_core.services.tenant.tenant_context import TenantContext

            ctx = TenantContext().get()
            if ctx and str(ctx).strip():
                doc.custom_heshly_tenant_id = str(ctx).strip()
                return
        except Exception:
            pass
        # 4. If Event was created from Appointment via create_calendar_event, participants contain Lead
        parts = getattr(doc, "event_participants", None) or []
        for p in parts:
            try:
                dt = getattr(p, "reference_doctype", None) or p.get("reference_doctype") if isinstance(p, dict) else None
                dn = getattr(p, "reference_docname", None) or p.get("reference_docname") if isinstance(p, dict) else None
                t = _infer_tenant_from_reference(dt, dn)
                if t and str(t).strip():
                    doc.custom_heshly_tenant_id = str(t).strip()
                    return
            except Exception:
                continue
    except Exception:
        pass
