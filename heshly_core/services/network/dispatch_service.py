"""Sequential exclusive lead dispatch — core of Layer 2."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC, timedelta
from typing import Any

from heshly_core.models.network import DispatchStatus, NetworkStatus, RoutingStatus
from heshly_core.services.network.settings_service import get_network_settings


def _now() -> datetime:
    # Frappe expects naive UTC for DB (without tzinfo), store naive
    return datetime.now(UTC).replace(tzinfo=None)


def _new_dispatch_id() -> str:
    return f"hdsp_{uuid.uuid4().hex[:10]}"


def _has_accepted(conversation_id: str, consult_task_id: str | None = None) -> bool:
    import frappe  # type: ignore
    flt: dict[str, Any] = {"network_conversation_id": conversation_id, "status": DispatchStatus.ACCEPTED.value}
    if consult_task_id is not None:
        flt["consult_task_id"] = consult_task_id
        return bool(frappe.db.exists("Heshly Network Dispatch", flt))
    # Legacy: conversation-level check includes NULL-task dispatches
    # For task-scoped callers, pass consult_task_id explicitly
    return bool(frappe.db.exists("Heshly Network Dispatch", flt))


def _dispatched_tenant_ids(conversation_id: str, consult_task_id: str | None = None) -> set[str]:
    import frappe  # type: ignore
    try:
        flt: dict[str, Any] = {"network_conversation_id": conversation_id}
        if consult_task_id is not None:
            flt["consult_task_id"] = consult_task_id
        rows = frappe.get_all("Heshly Network Dispatch", filters=flt, fields=["tenant_id"])
        return {r["tenant_id"] for r in rows}
    except Exception as e:
        # Column not yet migrated (consult_task_id) — fallback to conversation-level
        if "consult_task_id" in str(e) or "Unknown column" in str(e):
            try:
                rows = frappe.get_all("Heshly Network Dispatch", filters={"network_conversation_id": conversation_id}, fields=["tenant_id"])
                return {r["tenant_id"] for r in rows}
            except: return set()
        return set()


def _has_offered_for_task(conversation_id: str, consult_task_id: str) -> bool:
    import frappe  # type: ignore
    try:
        return bool(frappe.db.exists("Heshly Network Dispatch", {"network_conversation_id": conversation_id, "consult_task_id": consult_task_id, "status": ["in", [DispatchStatus.OFFERED.value, DispatchStatus.ACCEPTED.value]]}))
    except Exception as e:
        if "consult_task_id" in str(e) or "Unknown column" in str(e):
            return False
        return False


def cancel_task_dispatches(network_conversation_id: str, consult_task_id: str) -> None:
    import frappe  # type: ignore
    try:
        rows = frappe.get_all("Heshly Network Dispatch", filters={"network_conversation_id": network_conversation_id, "consult_task_id": consult_task_id, "status": DispatchStatus.OFFERED.value}, fields=["name"])
    except Exception as e:
        if "consult_task_id" in str(e) or "Unknown column" in str(e):
            return
        return
    for r in rows:
        try:
            d = frappe.get_doc("Heshly Network Dispatch", r["name"])
            d.status = DispatchStatus.CANCELLED.value
            d.save(ignore_permissions=True)
        except Exception:
            pass
    try:
        frappe.db.commit()
    except Exception:
        try: frappe.db.rollback()
        except: pass


def offer_next_for_task(network_conversation_id: str, consult_task_id: str, candidates: list[Any] | None = None) -> Any | None:
    """Task-aware offer — matches/dispatches strictly for the given consult_task_id."""
    import frappe  # type: ignore
    from heshly_core.services.network.matching_engine import rank_candidates, enrich_from_frappe, filter_eligible_candidates
    from heshly_core.services.network.consultation_engine import _load_tasks
    import json as _j
    conv = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": network_conversation_id})
    qd = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
    tasks = _load_tasks(qd)
    task = next((t for t in tasks if t.task_id == consult_task_id), None)
    if task is None:
        return None
    if (task.location or "").strip() == "":
        return None
    if _has_offered_for_task(network_conversation_id, consult_task_id):
        return None
    if candidates is None:
        memberships = frappe.get_all("Heshly Network Membership", filters={"status": "Active", "accepts_network_leads": 1}, fields=["*"])
        already = _dispatched_tenant_ids(network_conversation_id, consult_task_id)
        memberships = [m for m in memberships if m.get("tenant_id") not in already]
        if not memberships:
            return None
        bmap, kmap, hmap = enrich_from_frappe(memberships)
        filtered = filter_eligible_candidates(conv, memberships, bmap, kmap, consult_task=task)
        if not filtered:
            return None
        candidates = rank_candidates(conv, filtered, bmap, kmap, hmap, consult_task=task)
    already = _dispatched_tenant_ids(network_conversation_id, consult_task_id)
    chosen = None
    for c in candidates:
        if c.tenant_id not in already and c.score > 0:
            chosen = c; break
    if not chosen:
        return None
    from heshly_core.services.network.settings_service import get_network_settings as _gset
    settings = _gset()
    now = _now(); deadline = now + timedelta(seconds=int(settings.dispatch_timeout_seconds or 300))
    try:
        dispatch = frappe.get_doc({"doctype": "Heshly Network Dispatch", "dispatch_id": _new_dispatch_id(), "network_conversation_id": network_conversation_id, "consult_task_id": consult_task_id, "tenant_id": chosen.tenant_id, "business_id": chosen.business_id, "status": DispatchStatus.OFFERED.value, "attempt_index": 1, "ranking_score": float(chosen.score), "ranking_reasons": json.dumps(chosen.reasons, ensure_ascii=False)[:2000], "offered_at": now, "deadline_at": deadline, "lead_fee": float(settings.default_lead_fee or 0), "billing_status": "pending"})
        dispatch.insert(ignore_permissions=True)
    except Exception as e:
        if "consult_task_id" in str(e) or "Unknown column" in str(e):
            # Column not yet migrated — fallback to legacy insert without task_id
            dispatch = frappe.get_doc({"doctype": "Heshly Network Dispatch", "dispatch_id": _new_dispatch_id(), "network_conversation_id": network_conversation_id, "tenant_id": chosen.tenant_id, "business_id": chosen.business_id, "status": DispatchStatus.OFFERED.value, "attempt_index": 1, "ranking_score": float(chosen.score), "ranking_reasons": json.dumps(chosen.reasons, ensure_ascii=False)[:2000], "offered_at": now, "deadline_at": deadline, "lead_fee": float(settings.default_lead_fee or 0), "billing_status": "pending"})
            dispatch.insert(ignore_permissions=True)
        else:
            raise
    frappe.db.commit()
    try:
        from heshly_core.services.network.notification_service import notify_business
        notify_business(dispatch, conv)
    except: pass
    return dispatch


def offer_next(network_conversation_id: str, candidates: list[Any] | None = None) -> Any | None:
    """
    Legacy conversation-level offer — delegates to active task for backward compat.
    For multi-task conversations, prefer offer_next_for_task per task.
    """
    import frappe  # type: ignore
    from heshly_core.services.network.matching_engine import rank_candidates, enrich_from_frappe

    if _has_accepted(network_conversation_id):
        return None

    conv = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": network_conversation_id})
    settings = get_network_settings()
    timeout = int(settings.dispatch_timeout_seconds or 300)
    max_attempts = int(settings.max_dispatch_attempts or 5)

    if int(getattr(conv, "offer_attempt", 0) or 0) >= max_attempts:
        try:
            conv.network_status = NetworkStatus.TIMED_OUT.value
            conv.routing_status = RoutingStatus.FAILED.value
            conv.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
        return None

    already = _dispatched_tenant_ids(network_conversation_id)

    if candidates is None:
        # build candidates from active memberships
        memberships = frappe.get_all("Heshly Network Membership", filters={"status": "Active", "accepts_network_leads": 1}, fields=["*"])
        # filter out already dispatched
        memberships = [m for m in memberships if m.get("tenant_id") not in already]
        if not memberships:
            try:
                conv.network_status = NetworkStatus.TIMED_OUT.value
                conv.routing_status = RoutingStatus.FAILED.value
                conv.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                frappe.db.rollback()
            return None
        bmap, kmap, hmap = enrich_from_frappe(memberships)
        # Geographic eligibility gate (ND-04): filter before ranking
        from heshly_core.services.network.matching_engine import filter_eligible_candidates  # local to avoid cycle
        filtered = filter_eligible_candidates(conv, memberships, bmap, kmap)
        if not filtered:
            # No eligible businesses in requested area → fallback (same as no candidates)
            try:
                conv.network_status = NetworkStatus.TIMED_OUT.value
                conv.routing_status = RoutingStatus.FAILED.value
                conv.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                frappe.db.rollback()
            return None
        candidates = rank_candidates(conv, filtered, bmap, kmap, hmap)

    # pick first candidate not yet dispatched and with score > 0
    chosen = None
    for c in candidates:
        if c.tenant_id not in already and c.score > 0:
            chosen = c
            break
    if not chosen:
        try:
            conv.network_status = NetworkStatus.TIMED_OUT.value
            conv.routing_status = RoutingStatus.FAILED.value
            conv.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
        return None

    now = _now()
    deadline = now + timedelta(seconds=timeout)
    attempt = int(getattr(conv, "offer_attempt", 0) or 0) + 1

    dispatch = frappe.get_doc({
        "doctype": "Heshly Network Dispatch",
        "dispatch_id": _new_dispatch_id(),
        "network_conversation_id": network_conversation_id,
        "tenant_id": chosen.tenant_id,
        "business_id": chosen.business_id,
        "status": DispatchStatus.OFFERED.value,
        "attempt_index": attempt,
        "ranking_score": float(chosen.score),
        "ranking_reasons": json.dumps(chosen.reasons, ensure_ascii=False)[:2000],
        "offered_at": now,
        "deadline_at": deadline,
        "lead_fee": float(settings.default_lead_fee or 0),
        "billing_status": "pending",
    })
    dispatch.insert(ignore_permissions=True)

    try:
        conv.offer_attempt = attempt
        conv.network_status = NetworkStatus.OFFERED.value
        conv.routing_status = RoutingStatus.OFFERED.value
        conv.expires_at = deadline
        # persist ranked candidates snapshot (top 5)
        try:
            snap = [{"tenant_id": c.tenant_id, "business_id": c.business_id, "score": c.score} for c in candidates[:5]]
            conv.candidate_businesses = json.dumps(snap, ensure_ascii=False)[:8000]
            if getattr(conv, "qualification_state", "") == "pending":
                conv.qualification_state = "qualified"
            if conv.network_status == NetworkStatus.NEW.value:
                conv.network_status = NetworkStatus.MATCHED.value
        except Exception:
            pass
        conv.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        raise

    # notify business (best-effort)
    try:
        from heshly_core.services.network.notification_service import notify_business
        notify_business(dispatch, conv)
    except Exception:
        pass

    # website channel already renders its own assistant reply via website_chat;
    # avoid double-appending (website_chat appends its own dispatch-success reply).
    try:
        if str(getattr(conv, "channel", "") or "").lower() != "web":
            from heshly_core.services.network.notification_service import notify_customer_holding
            raw = getattr(conv, "_raw_user_text", None)
            if raw is not None:
                notify_customer_holding(conv, raw_user_text=str(raw))
            else:
                try:
                    turns = getattr(conv, "turns", []) or []
                    last_user = ""
                    for t in reversed(turns):
                        if getattr(t, "role", "") == "user":
                            last_user = str(getattr(t, "message", "") or "")
                            break
                    notify_customer_holding(conv, raw_user_text=last_user)
                except Exception:
                    notify_customer_holding(conv)
    except Exception:
        pass

    return dispatch


def accept_dispatch(dispatch_id: str, caller_tenant_id: str) -> dict[str, Any]:
    """Tenant accepts an offered dispatch. Returns {success, message}."""
    import frappe  # type: ignore
    from heshly_core.services.network import network_conversation_service as ncs
    d = frappe.get_doc("Heshly Network Dispatch", {"dispatch_id": dispatch_id})
    if not d:
        return {"success": False, "message": "Dispatch not found"}
    if str(getattr(d, "tenant_id", "")) != str(caller_tenant_id):
        return {"success": False, "message": "Not authorized for this dispatch"}
    if str(getattr(d, "status", "")) != DispatchStatus.OFFERED.value:
        return {"success": False, "message": f"Dispatch not offerable (status={getattr(d,'status','')})"}
    # deadline check — on expiry, re-offer same task
    try:
        deadline = getattr(d, "deadline_at", None)
        if deadline and _now() > deadline:
            d.status = DispatchStatus.TIMED_OUT.value
            d.responded_at = _now()
            d.save(ignore_permissions=True)
            frappe.db.commit()
            try:
                _tid = getattr(d, "consult_task_id", None)
                if _tid:
                    offer_next_for_task(str(getattr(d, "network_conversation_id", "")), str(_tid))
                else:
                    offer_next(str(getattr(d, "network_conversation_id", "")))
            except Exception:
                pass
            return {"success": False, "message": "Offer expired — reassigned"}
    except Exception:
        pass
    # Task-scoped: only block if same task already accepted; legacy NULL tasks fall back to conversation check
    _tid = getattr(d, "consult_task_id", None)
    if _tid:
        if _has_accepted(str(getattr(d, "network_conversation_id", "")), str(_tid)):
            return {"success": False, "message": "Lead already assigned to another business for this task"}
    else:
        if _has_accepted(str(getattr(d, "network_conversation_id", ""))):
            return {"success": False, "message": "Lead already assigned to another business"}
    # Task-scoped accept must not lock whole conversation; only legacy NULL tasks use conversation-level assign
    if _tid:
        # Mark task as referred in qualification_data, do not set conversation-level assigned_tenant_id
        try:
            import json as _j2
            from heshly_core.services.network.consultation_engine import _load_tasks as _lt2, _save_tasks as _st2
            conv2 = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": str(getattr(d, "network_conversation_id", ""))})
            qd2 = json.loads(getattr(conv2, "qualification_data", "") or "{}") if getattr(conv2, "qualification_data", "") else {}
            tasks2 = _lt2(qd2)
            for _t2 in tasks2:
                if _t2.task_id == str(_tid):
                    _t2.referral_state = "accepted"
                    _t2.status = "referred"
                    break
            conv2.qualification_data = json.dumps(_st2(qd2, tasks2), ensure_ascii=False)[:10000]
            conv2.save(ignore_permissions=True)
        except Exception:
            pass
    else:
        conv = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": str(getattr(d, "network_conversation_id", ""))})
        ok = ncs.assign_to_tenant(conv, caller_tenant_id, getattr(d, "business_id", None))
        if not ok:
            return {"success": False, "message": "Lead already assigned"}
    d.status = DispatchStatus.ACCEPTED.value
    d.responded_at = _now()
    d.response_channel = "portal"
    d.save(ignore_permissions=True)
    # Cancel only other OFFERED for same task (not whole conversation)
    try:
        flt2: dict[str, Any] = {"network_conversation_id": getattr(d, "network_conversation_id"), "status": DispatchStatus.OFFERED.value}
        if _tid:
            flt2["consult_task_id"] = _tid
        others = frappe.get_all("Heshly Network Dispatch", filters=flt2, fields=["name", "dispatch_id"])
        for o in others:
            if o.get("dispatch_id") == dispatch_id:
                continue
            try:
                od = frappe.get_doc("Heshly Network Dispatch", o["name"])
                od.status = DispatchStatus.CANCELLED.value
                od.save(ignore_permissions=True)
            except Exception:
                pass
    except Exception:
        pass
    # bump membership accepted counter
    try:
        m = frappe.db.get_value("Heshly Network Membership", {"tenant_id": caller_tenant_id}, ["name"], as_dict=False)
        if m:
            frappe.db.sql("UPDATE `tabHeshly Network Membership` SET total_leads_accepted = COALESCE(total_leads_accepted,0)+1 WHERE name=%s", (m,))
    except Exception:
        pass
    frappe.db.commit()
    # create tenant Lead (best-effort, additive)
    try:
        _create_tenant_lead(conv, caller_tenant_id)
    except Exception:
        pass
    try:
        from heshly_core.services.network.notification_service import notify_customer_assigned
        notify_customer_assigned(conv)
    except Exception:
        pass
    return {"success": True, "message": "Lead accepted", "network_conversation_id": str(getattr(d, "network_conversation_id", ""))}


def decline_dispatch(dispatch_id: str, caller_tenant_id: str) -> dict[str, Any]:
    import frappe  # type: ignore
    d = frappe.get_doc("Heshly Network Dispatch", {"dispatch_id": dispatch_id})
    if not d:
        return {"success": False, "message": "Dispatch not found"}
    if str(getattr(d, "tenant_id", "")) != str(caller_tenant_id):
        return {"success": False, "message": "Not authorized"}
    if str(getattr(d, "status", "")) != DispatchStatus.OFFERED.value:
        return {"success": False, "message": f"Cannot decline (status={getattr(d,'status','')})"}
    d.status = DispatchStatus.DECLINED.value
    d.responded_at = _now()
    d.response_channel = "portal"
    d.save(ignore_permissions=True)
    try:
        m = frappe.db.get_value("Heshly Network Membership", {"tenant_id": caller_tenant_id}, ["name"], as_dict=False)
        if m:
            frappe.db.sql("UPDATE `tabHeshly Network Membership` SET total_leads_declined = COALESCE(total_leads_declined,0)+1 WHERE name=%s", (m,))
    except Exception:
        pass
    frappe.db.commit()
    # Task-scoped re-offer using same task's service/location
    try:
        _tid2 = getattr(d, "consult_task_id", None)
        if _tid2:
            offer_next_for_task(str(getattr(d, "network_conversation_id", "")), str(_tid2))
        else:
            offer_next(str(getattr(d, "network_conversation_id", "")))
    except Exception:
        pass
    return {"success": True, "message": "Lead declined — offered to next business"}


def _create_tenant_lead(conv: Any, tenant_id: str) -> None:
    """Create Lead in tenant CRM (additive, uses ignore_permissions)."""
    import frappe  # type: ignore
    phone = getattr(conv, "customer_phone", "") or ""
    name = getattr(conv, "customer_name", "") or phone
    # ERPNext Lead uses custom_heshly_tenant_id for isolation; notes is child table, cannot set as string
    try:
        lead = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": name,
            "mobile_no": phone,
            "phone": phone,
            "status": "Lead",
            "custom_heshly_tenant_id": tenant_id,
        })
        lead.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        # fallback: minimal fields
        try:
            lead = frappe.get_doc({
                "doctype": "Lead",
                "lead_name": name,
                "mobile_no": phone,
                "status": "Lead",
            })
            lead.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
