from __future__ import annotations

import frappe

from heshly_core.models.crm import LeadStatus
from heshly_core.models.qualification import QualificationResult
from heshly_core.repositories.repository_factory import repository_factory
from heshly_core.services.tenant.tenant_context import TenantContext


def _norm_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    p = str(phone).strip()
    if not p:
        return None
    # canonicalize: digits only with leading +
    digits = "".join(c for c in p if c.isdigit())
    if not digits:
        return None
    if p.strip().startswith("+"):
        return "+" + digits
    # ERPNext stores like 2547..., WhatsApp is +254
    if digits.startswith("254"):
        return "+" + digits
    return p


def persist_qualification_to_lead(
    tenant_id: str,
    customer_name: str | None,
    phone: str | None,
    email: str | None,
    qual_result: QualificationResult | None,
    source: str = "whatsapp",
) -> dict | None:
    """Create or update Lead for tenant, persisting qualification score/status.

    - Dedup by phone (mobile_no) then email within tenant+active statuses, else by created phone.
    - Does not create duplicates when same conversation continues.
    - Uses qualification_engine as source of truth (passed qual_result).
    - Maps QualificationStatus -> LeadStatus: qualified->QUALIFIED, collecting_info->CONTACTED/new stays, not_qualified/escalated->UNQUALIFIED appropriately.
    - Preserves ERPNext semantics via LeadRepository._status_to_frappe (QUALIFIED -> Opportunity).
    """
    if not tenant_id or not str(tenant_id).strip():
        return None
    tenant_id = str(tenant_id).strip()

    # Need at least phone or name to identify lead
    if not phone and not customer_name and not email:
        return None

    TenantContext().set(tenant_id)
    repo = repository_factory.leads

    # Find existing active lead for this customer in tenant
    existing = None
    if phone:
        # Normalize both forms and try both
        try:
            existing = repo.find_by_phone(phone)
        except Exception:
            existing = None
        if not existing:
            # try normalized without +
            alt = _norm_phone(phone)
            if alt and alt != phone:
                try:
                    existing = repo.find_by_phone(alt)
                except Exception:
                    pass
                if not existing:
                    # search by raw digits without +
                    try:
                        existing = repo.find_by_phone(alt.lstrip("+"))
                    except Exception:
                        pass
        # fallback: search via phone full
        if not existing:
            try:
                rows = repo.search(phone)
                for r in rows:
                    if r.phone and phone and r.phone.replace(" ", "") in phone.replace(" ", "") or phone in r.phone:
                        existing = r
                        break
                if not existing and rows:
                    # If search returned leads but none matched, pick most recent active for same tenant
                    active = {LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED}
                    for r in rows:
                        if r.status in active:
                            existing = r
                            break
            except Exception:
                pass
    if not existing and email:
        try:
            existing = repo.find_by_email(email)
        except Exception:
            pass
    # If still not found but we have a name, search by lead_name within tenant (handles multi-turn where phone added later)
    if not existing and customer_name:
        try:
            # Prefer the most recent active lead with same name
            rows = frappe.get_all(
                "Lead",
                filters={"custom_heshly_tenant_id": tenant_id, "lead_name": customer_name},
                fields=["name"],
                order_by="creation desc",
                limit=5,
            )
            for r in rows:
                try:
                    cand = repo.get(r["name"] if isinstance(r, dict) else r.name)
                except Exception:
                    cand = None
                if cand and cand.status in {LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED}:
                    existing = cand
                    break
            if not existing and rows:
                # fallback to most recent regardless of status
                try:
                    existing = repo.get(rows[0]["name"] if isinstance(rows[0], dict) else rows[0].name)
                except Exception:
                    pass
        except Exception:
            pass

    # Determine target status/score from qual_result
    score = int(getattr(qual_result, "score", 0) or 0) if qual_result else 0
    qstatus = getattr(qual_result, "status", None).value if qual_result and hasattr(qual_result.status, "value") else None

    # Map qualification to LeadStatus per task:
    # - New unqualified inquiry -> Lead (NEW)
    # - Partially qualified (collecting_info) -> Open/CONTACTED (still not fully qualified)
    # - Fully qualified -> Opportunity/QUALIFIED
    target_status = None
    if qstatus == "qualified":
        target_status = LeadStatus.QUALIFIED
    elif qstatus == "collecting_info":
        # Partially qualified -> CONTACTED (Open in ERPNext) if we have phone/name
        target_status = LeadStatus.CONTACTED
    elif qstatus in ("not_qualified", "escalated"):
        # For now keep as NEW unless was qualified before; do not mark LOST automatically
        target_status = LeadStatus.UNQUALIFIED if qstatus == "not_qualified" else None
        # Escalated stays as is (don't downgrade qualified)
    else:
        # unknown -> keep NEW
        target_status = None

    if existing:
        # Update existing lead in place — never duplicate
        updated = False
        if customer_name and customer_name.strip() and customer_name.strip() != existing.full_name:
            existing.full_name = customer_name.strip()
            updated = True
        if phone and phone.strip() and phone.strip() != existing.phone:
            # Update phone if we now have a better one
            existing.phone = phone.strip()
            updated = True
        if email and email.strip().lower() != (existing.email or "").lower():
            existing.email = email.strip().lower()
            updated = True
        if score != existing.score:
            existing.score = score
            updated = True
        if target_status and target_status != existing.status:
            # Use status manager to enforce valid transitions
            try:
                from heshly_core.services.crm.lead_status_manager import LeadStatusManager
                mgr = LeadStatusManager()
                mgr.change_status(existing, target_status)
                # change_status already mutates existing.status
                updated = True
            except Exception:
                # Force if transition disallowed for auto-qualification (e.g., NEW->QUALIFIED now allowed, but fallback)
                if existing.status != target_status:
                    existing.status = target_status
                    updated = True
        elif updated:
            pass
        if updated:
            existing.updated_at = frappe.utils.now_datetime() if hasattr(frappe.utils, "now_datetime") else existing.updated_at
            try:
                repo.save(existing)
            except Exception as e:
                frappe.logger().warning(f"persist_qualification_to_lead save failed: {e}")
                # Don't throw
                pass
        return {"lead": existing, "created": False}

    # No existing: create new Lead
    full_name = (customer_name or phone or email or "Customer").strip() or "Customer"
    norm_phone = phone.strip() if phone else None
    norm_email = email.strip().lower() if email else None
    from heshly_core.services.crm.lead_creator import LeadCreator
    creator = LeadCreator(repository=repo)
    try:
        lead = creator.create(
            business_id=tenant_id,
            full_name=full_name,
            phone=norm_phone,
            email=norm_email,
            source=source,
        )
        # Apply score/status after creation (creator starts as NEW/0)
        lead.score = score
        if target_status and target_status != lead.status:
            try:
                from heshly_core.services.crm.lead_status_manager import LeadStatusManager
                mgr = LeadStatusManager()
                # Allow NEW->CONTACTED or NEW->QUALIFIED
                mgr.change_status(lead, target_status)
            except Exception:
                lead.status = target_status
        # Save mutated
        try:
            repo.save(lead)
        except Exception:
            pass
        return {"lead": lead, "created": True}
    except Exception as e:
        frappe.logger().warning(f"persist_qualification_to_lead create failed: {e}")
        return None
