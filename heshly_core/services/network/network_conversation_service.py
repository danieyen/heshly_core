"""Network conversation persistence — mirrors AI Conversation pattern."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC
from typing import Any

from heshly_core.models.network import NetworkStatus, RoutingStatus


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _new_id(phone: str) -> str:
    return f"hnet_{uuid.uuid4().hex[:12]}"


def _safe_json_loads(v: Any, default=None):
    if v is None or v == "":
        return default if default is not None else {}
    if isinstance(v, dict):
        return v
    if isinstance(v, list):
        return v
    try:
        return json.loads(v)
    except Exception:
        return default if default is not None else {}


def get_or_create_conversation(
    customer_phone: str,
    customer_name: str | None = None,
    source_phone_number_id: str | None = None,
    channel: str = "whatsapp",
) -> Any:
    """Get existing open conversation for customer_phone or create new. Returns Frappe doc."""
    import frappe  # type: ignore
    phone = str(customer_phone).strip()
    # Reuse most recent non-terminal conversation for this phone
    terminal = [NetworkStatus.COMPLETED.value, NetworkStatus.CANCELLED.value, NetworkStatus.ACCEPTED.value]
    existing = frappe.db.get_value(
        "Heshly Network Conversation",
        {"customer_phone": phone, "network_status": ["not in", terminal]},
        ["name", "network_conversation_id"],
        as_dict=True,
        order_by="modified desc",
    )
    if existing and existing.get("name"):
        try:
            return frappe.get_doc("Heshly Network Conversation", existing["name"])
        except Exception:
            pass
    nid = _new_id(phone)
    doc = frappe.get_doc({
        "doctype": "Heshly Network Conversation",
        "network_conversation_id": nid,
        "customer_phone": phone,
        "customer_name": customer_name or "",
        "channel": channel,
        "network_status": NetworkStatus.NEW.value,
        "qualification_state": "pending",
        "routing_status": RoutingStatus.IDLE.value,
        "offer_attempt": 0,
        "turn_count": 0,
        "source_phone_number_id": source_phone_number_id or "",
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


def reset_for_new_request(doc: Any) -> Any:
    """Close the current conversation and open a fresh one for the next substantive request.

    Called when the customer sends a genuine greeting or explicit reset.
    Preserves history by marking the old row CANCELLED and inserting a new row.
    Returns the new doc. Idempotent — if doc is already in a terminal state, returns doc as-is.
    """
    import frappe  # type: ignore
    import json as _json
    terminal = {NetworkStatus.COMPLETED.value, NetworkStatus.CANCELLED.value, NetworkStatus.ACCEPTED.value}
    if str(getattr(doc, "network_status", "")) in terminal:
        return doc
    # If no service context is stored, there is nothing to reset — just greet on this doc.
    if not getattr(doc, "requested_service", "") and not getattr(doc, "location", ""):
        # Don't churn rows for pure hi→hi: still return same doc but clear pending timers.
        return doc
    try:
        doc.network_status = NetworkStatus.CANCELLED.value
        doc.routing_status = RoutingStatus.IDLE.value
        doc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        try:
            frappe.db.rollback()
        except Exception:
            pass
        return doc
    # Cancel any pending OFFERED dispatches for the closed conversation so a future
    # "genuine greeting with no substantive next message" cannot leave a dangling offer.
    try:
        _cancel_offered_dispatches(str(getattr(doc, "network_conversation_id", "")))
    except Exception:
        pass
    nid = _new_id(str(getattr(doc, "customer_phone", "")).strip())
    new_doc = frappe.get_doc({
        "doctype": "Heshly Network Conversation",
        "network_conversation_id": nid,
        "customer_phone": str(getattr(doc, "customer_phone", "")).strip(),
        "customer_name": str(getattr(doc, "customer_name", "") or "").strip(),
        "channel": str(getattr(doc, "channel", "") or "whatsapp"),
        "network_status": NetworkStatus.NEW.value,
        "qualification_state": "pending",
        "routing_status": RoutingStatus.IDLE.value,
        "offer_attempt": 0,
        "turn_count": 0,
        "source_phone_number_id": str(getattr(doc, "source_phone_number_id", "") or ""),
        "qualification_data": "",
        "requested_service": "",
        "location": "",
    })
    new_doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return new_doc


def _cancel_offered_dispatches(network_conversation_id: str) -> None:
    import frappe  # type: ignore
    from heshly_core.models.network import DispatchStatus
    try:
        rows = frappe.get_all("Heshly Network Dispatch", filters={"network_conversation_id": network_conversation_id, "status": DispatchStatus.OFFERED.value}, fields=["name"])
        for r in rows:
            try:
                d = frappe.get_doc("Heshly Network Dispatch", r["name"])
                d.status = DispatchStatus.CANCELLED.value
                d.save(ignore_permissions=True)
            except Exception:
                continue
        frappe.db.commit()
    except Exception:
        try:
            frappe.db.rollback()
        except Exception:
            pass


def append_turn(doc: Any, role: str, message: str, intent: str | None = None) -> None:
    import frappe  # type: ignore
    try:
        doc.append("turns", {
            "role": role,
            "message": message,
            "intent": intent or "",
            "timestamp": _now(),
        })
        doc.turn_count = int(getattr(doc, "turn_count", 0) or 0) + 1
        doc.last_message_at = _now()
        doc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        raise


def set_qualification(doc: Any, data: dict[str, Any]) -> None:
    import frappe  # type: ignore
    try:
        # Raw / normalized: clear when pop-driven (reset/casual cleared), otherwise keep existing if not in data
        # For casual/greeting/reset we explicitly want to clear stale service/location/categories
        if "raw_request" in data:
            try:
                if data.get("raw_request"):
                    doc.raw_request = str(data["raw_request"])[:500]
                elif data.get("raw_request") == "":
                    doc.raw_request = ""
            except Exception:
                pass
        elif data.get("raw_request") is None and "requested_service" not in data:
            pass  # keep existing raw_request unless explicitly cleared
        if "normalized_service" in data:
            try:
                doc.normalized_service = str(data["normalized_service"] or "")[:140] if data.get("normalized_service") else ""
            except Exception:
                pass
        if "provider_category" in data:
            try:
                doc.provider_category = str(data["provider_category"] or "")[:140] if data.get("provider_category") else ""
            except Exception:
                pass
        elif "normalized_service" in data and not data.get("normalized_service"):
            try:
                doc.normalized_service = ""
                doc.provider_category = ""
            except Exception:
                pass
        # Always reflect requested_service/normalized if present in data (including empty string to clear)
        if "requested_service" in data:
            try:
                doc.requested_service = str(data["requested_service"] or "")[:140] if data.get("requested_service") else ""
            except Exception:
                pass
        elif not data.get("requested_service") and data.get("qualification_state") == "pending" and not data.get("location"):
            # Pending casual/greeting: explicitly clear stale service even if data has no key
            try:
                doc.requested_service = ""
                doc.normalized_service = ""
                doc.provider_category = ""
            except Exception:
                pass
        if "normalized_service" in data:
            try:
                doc.normalized_service = str(data["normalized_service"] or "")[:140] if data.get("normalized_service") is not None else ""
                # also clear provider if normalized cleared
                if not data.get("normalized_service"):
                    doc.provider_category = ""
            except Exception:
                pass
        if "provider_category" in data:
            try:
                doc.provider_category = str(data["provider_category"] or "")[:140] if data.get("provider_category") is not None else ""
            except Exception:
                pass
        elif "normalized_service" in data and not data.get("normalized_service"):
            try:
                doc.provider_category = ""
            except Exception:
                pass
        # Second pass for legacy requested_service duplication (harmless)
        # Location: write when present, explicitly clear on pending-reset with empty location
        if "location" in data:
            try:
                doc.location = str(data["location"] or "")[:140] if data.get("location") else ""
            except Exception:
                pass
        elif data.get("qualification_state") == "pending" and data.get("location") is None:
            try:
                doc.location = ""
            except Exception:
                pass
        if data.get("urgency"):
            doc.urgency = str(data["urgency"]).lower()
        if data.get("preferred_time"):
            doc.preferred_time = str(data["preferred_time"])[:140]
        if data.get("budget_min") is not None:
            try:
                doc.budget_min = float(data["budget_min"])
            except Exception:
                pass
        elif data.get("qualification_state") == "pending" and data.get("budget_min") is None:
            try:
                doc.budget_min = 0
            except Exception:
                pass
        if data.get("budget_max") is not None:
            try:
                doc.budget_max = float(data["budget_max"])
            except Exception:
                pass
        # Capacity: persisted inside qualification_data JSON; also clear explicitly on pending reset so old capacity does not linger
        if data.get("capacity") is not None:
            try:
                # stored in qualification_data; no dedicated column, but ensure it is written
                pass
            except Exception:
                pass
        if data.get("qualification_state"):
            doc.qualification_state = str(data["qualification_state"])
        # store full JSON
        try:
            doc.qualification_data = json.dumps(data, ensure_ascii=False)[:10000]
        except Exception:
            pass
        # status progression
        qs = str(data.get("qualification_state") or "")
        if qs == "qualified" and doc.network_status == NetworkStatus.NEW.value:
            doc.network_status = NetworkStatus.QUALIFYING.value
            # will move to QUALIFIED after matching
        doc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        raise


def set_status(doc: Any, network_status: str, routing_status: str | None = None) -> None:
    import frappe  # type: ignore
    try:
        doc.network_status = network_status
        if routing_status:
            doc.routing_status = routing_status
        doc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        raise


def assign_to_tenant(doc: Any, tenant_id: str, business_id: str | None = None) -> bool:
    """Atomic assign — returns False if already assigned to another tenant."""
    import frappe  # type: ignore
    try:
        frappe.db.sql("SELECT name FROM `tabHeshly Network Conversation` WHERE name=%s FOR UPDATE", (doc.name,))
        fresh = frappe.get_doc("Heshly Network Conversation", doc.name)
        if getattr(fresh, "assigned_tenant_id", None):
            return False
        fresh.assigned_tenant_id = tenant_id
        fresh.assigned_business_id = business_id or tenant_id
        fresh.assigned_at = _now()
        fresh.network_status = NetworkStatus.ACCEPTED.value
        fresh.routing_status = RoutingStatus.ASSIGNED.value
        fresh.save(ignore_permissions=True)
        frappe.db.commit()
        # reflect on passed doc
        doc.assigned_tenant_id = fresh.assigned_tenant_id
        doc.assigned_business_id = fresh.assigned_business_id
        doc.assigned_at = fresh.assigned_at
        doc.network_status = fresh.network_status
        doc.routing_status = fresh.routing_status
        return True
    except Exception:
        frappe.db.rollback()
        raise
