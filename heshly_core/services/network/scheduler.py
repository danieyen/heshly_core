"""Frappe scheduler — reconciles timed-out dispatches (additive, idempotent)."""

from __future__ import annotations

from datetime import datetime, UTC


def reconcile_timeouts() -> dict:
    """Hourly/all job: timeout expired OFFERED dispatches and reassign."""
    try:
        import frappe  # type: ignore
        from heshly_core.models.network import DispatchStatus
        now = datetime.now(UTC).replace(tzinfo=None)
        # for comparison normalize both to UTC-aware if needed handled below
        rows = frappe.get_all("Heshly Network Dispatch", filters={"status": DispatchStatus.OFFERED.value}, fields=["name", "dispatch_id", "network_conversation_id", "deadline_at", "tenant_id"])
        timed_out = 0
        for r in rows:
            dl = r.get("deadline_at")
            try:
                # both now and dl are naive UTC; direct compare is safe
                if dl and now > dl:
                    d = frappe.get_doc("Heshly Network Dispatch", r["name"])
                    if d.status != DispatchStatus.OFFERED.value:
                        continue
                    d.status = DispatchStatus.TIMED_OUT.value
                    d.responded_at = now
                    d.save(ignore_permissions=True)
                    try:
                        m = frappe.db.get_value("Heshly Network Membership", {"tenant_id": r.get("tenant_id")}, ["name"], as_dict=False)
                        if m:
                            frappe.db.sql("UPDATE `tabHeshly Network Membership` SET total_leads_timed_out = COALESCE(total_leads_timed_out,0)+1 WHERE name=%s", (m,))
                    except Exception:
                        pass
                    frappe.db.commit()
                    timed_out += 1
                    try:
                        from heshly_core.services.network.notification_service import notify_timeout
                        conv = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": r.get("network_conversation_id")})
                        notify_timeout(r.get("tenant_id") or "", conv)
                    except Exception:
                        pass
                    try:
                        from heshly_core.services.network.dispatch_service import offer_next
                        offer_next(str(r.get("network_conversation_id") or ""))
                    except Exception:
                        pass
            except Exception:
                continue
        return {"success": True, "timed_out": timed_out}
    except Exception as e:
        try:
            import frappe  # type: ignore
            frappe.logger().error(f"network reconcile_timeouts failed: {e}")
        except Exception:
            pass
        return {"success": False, "error": str(e)}
