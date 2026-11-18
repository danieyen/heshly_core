from __future__ import annotations

import frappe

from heshly_core.models.crm import Lead, LeadStatus
from heshly_core.repositories.repository_factory import repository_factory
from heshly_core.services.crm.lead_creator import LeadCreator


def _repository():
    return repository_factory.leads


def _serialize(customer: Lead) -> dict:
    return {
        "id": customer.lead_id,
        "name": customer.full_name,
        "phone": customer.phone,
        "email": customer.email,
        "company": customer.company,
        "status": (
            customer.status.value
            if hasattr(customer.status, "value")
            else str(customer.status)
        ),
        "score": customer.score,
        "source": customer.source,
        "assigned_to": customer.assigned_to,
        "created_at": (
            customer.created_at.isoformat()
            if customer.created_at
            else None
        ),
        "updated_at": (
            customer.updated_at.isoformat()
            if customer.updated_at
            else None
        ),
    }


def _status(value: str | None) -> LeadStatus:
    value = (value or "new").strip().lower()

    try:
        return LeadStatus(value)
    except ValueError:
        frappe.throw(f"Invalid customer status: {value}")


@frappe.whitelist()
def list_customers():
    from heshly_core.services.tenant.tenant_context import TenantContext
    TenantContext().require()
    customers = _repository().list()

    return {
        "items": [_serialize(customer) for customer in customers],
        "total": len(customers),
    }


@frappe.whitelist()
def get_customer(customer_id: str):
    if not customer_id:
        frappe.throw("customer_id is required")

    from heshly_core.services.tenant.tenant_context import TenantContext
    TenantContext().require()

    customer = _repository().get(customer_id)

    if not customer:
        frappe.throw(
            f"Customer '{customer_id}' was not found."
        )

    return _serialize(customer)


@frappe.whitelist(allow_guest=True)
def search_customers(
    query: str | None = None,
    tenant_id: str | None = None,
):
    query = (query or "").strip()
    tenant_id = tenant_id.strip() if tenant_id else None

    if not tenant_id:
        frappe.throw("tenant_id is required")

    from heshly_core.services.tenant.tenant_context import TenantContext

    TenantContext().set(tenant_id)

    customers = (
        _repository().search(query)
        if query
        else _repository().list()
    )

    return {
        "items": [_serialize(customer) for customer in customers],
        "total": len(customers),
    }


@frappe.whitelist(allow_guest=True)
def create_customer(
    full_name: str,
    phone: str | None = None,
    email: str | None = None,
    company: str | None = None,
    source: str = "whatsapp",
    tenant_id: str | None = None,
):
    if not full_name or not full_name.strip():
        frappe.throw("full_name is required")

    tenant_id = tenant_id.strip() if tenant_id else None

    if not tenant_id:
        frappe.throw("tenant_id is required")

    from heshly_core.services.tenant.tenant_context import TenantContext

    TenantContext().set(tenant_id)

    customer = LeadCreator(
        repository=_repository()
    ).create(
        business_id=tenant_id,
        full_name=full_name.strip(),
        phone=phone.strip() if phone else None,
        email=email.strip().lower() if email else None,
        company=company.strip() if company else None,
        source=source,
    )

    return _serialize(customer)

@frappe.whitelist()
def update_customer(
    customer_id: str,
    full_name: str,
    phone: str | None = None,
    email: str | None = None,
    company: str | None = None,
    status: str = "new",
):
    if not customer_id:
        frappe.throw("customer_id is required")

    if not full_name or not full_name.strip():
        frappe.throw("full_name is required")

    from heshly_core.services.tenant.tenant_context import TenantContext
    TenantContext().require()

    customer = _repository().get(customer_id)

    if not customer:
        frappe.throw(
            f"Customer '{customer_id}' was not found."
        )

    customer.full_name = full_name.strip()
    customer.phone = phone.strip() if phone else None
    customer.email = email.strip().lower() if email else None
    customer.company = company.strip() if company else None
    customer.status = _status(status)

    saved = _repository().save(customer)

    return _serialize(saved)


@frappe.whitelist()
def delete_customer(customer_id: str):
    if not customer_id:
        frappe.throw("customer_id is required")

    from heshly_core.services.tenant.tenant_context import TenantContext
    TenantContext().require()

    deleted = _repository().delete(customer_id)

    if not deleted:
        frappe.throw(
            f"Customer '{customer_id}' was not found."
        )

    return {
        "success": True,
        "customer_id": customer_id,
    }

@frappe.whitelist(allow_guest=True)
def find_active_lead(
    phone=None,
    email=None,
    tenant_id=None,
):
    phone = phone.strip() if phone else None
    email = email.strip().lower() if email else None
    tenant_id = tenant_id.strip() if tenant_id else None

    if not phone and not email:
        frappe.throw("phone or email is required")

    if not tenant_id:
        frappe.throw("tenant_id is required")

    from heshly_core.services.tenant.tenant_context import TenantContext

    TenantContext().set(tenant_id)

    conditions = [
        f"`{_repository().TENANT_FIELD}` = %s",
        "`status` IN (%s, %s, %s)",
    ]

    values = [
        tenant_id,
        "new",
        "contacted",
        "qualified",
    ]

    identity = []

    if phone:
        identity.append("`mobile_no` = %s")
        values.append(phone)

    if email:
        identity.append("`email_id` = %s")
        values.append(email)

    conditions.append("(" + " OR ".join(identity) + ")")

    sql = (
        f"SELECT `{_repository().ID_FIELD}` AS lead_id "
        f"FROM `tab{_repository().DOCTYPE}` "
        "WHERE " + " AND ".join(conditions) + " "
        "ORDER BY creation DESC "
        "LIMIT 1"
    )

    row = frappe.db.sql(
        sql,
        values,
        as_dict=True,
    )

    if not row:
        return {
            "found": False,
            "lead": None,
        }

    lead = _repository().get(row[0]["lead_id"])

    if not lead:
        return {
            "found": False,
            "lead": None,
        }

    return {
        "found": True,
        "lead": _serialize(lead),
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def update_lead(
    lead_id,
    full_name=None,
    phone=None,
    email=None,
    tenant_id=None,
):
    lead_id = lead_id.strip() if lead_id else None
    tenant_id = tenant_id.strip() if tenant_id else None

    if not lead_id:
        frappe.throw("lead_id is required")

    if not tenant_id:
        frappe.throw("tenant_id is required")

    from heshly_core.services.tenant.tenant_context import TenantContext

    TenantContext().set(tenant_id)

    doc = frappe.db.get_value(
        "Lead",
        {
            "name": lead_id,
            "custom_heshly_tenant_id": tenant_id,
        },
        "name",
    )

    if not doc:
        frappe.throw("Lead not found")

    lead_doc = frappe.get_doc(
        "Lead",
        doc,
    )

    if full_name:
        lead_doc.lead_name = full_name.strip()

    if phone:
        lead_doc.mobile_no = phone.strip()

    if email:
        lead_doc.email_id = email.strip().lower()

    lead_doc.source = "WhatsApp"

    lead_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "lead": {
            "id": lead_doc.name,
            "heshly_lead_id": lead_doc.custom_heshly_lead_id,
            "tenant_id": lead_doc.custom_heshly_tenant_id,
            "name": lead_doc.lead_name,
            "phone": lead_doc.mobile_no,
            "email": lead_doc.email_id,
        },
    }


@frappe.whitelist(allow_guest=True)
def find_or_create_lead(phone=None, full_name=None, tenant_id=None, email=None, company=None, source="whatsapp"):
    phone = phone.strip() if phone else None
    full_name = full_name.strip() if full_name else None
    tenant_id = tenant_id.strip() if tenant_id else None
    email = email.strip().lower() if email else None
    company = company.strip() if company else None

    if not phone:
        frappe.throw("phone is required")
    if not tenant_id:
        frappe.throw("tenant_id is required")

    from heshly_core.services.tenant.tenant_context import TenantContext
    TenantContext().set(tenant_id)

    existing = _repository().search(phone)
    active_statuses = {LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED}

    for lead in existing:
        if lead.phone == phone and lead.status in active_statuses:
            return {"found": True, "created": False, "lead": _serialize(lead)}

    if not full_name:
        full_name = phone

    lead = LeadCreator(repository=_repository()).create(
        business_id=tenant_id,
        full_name=full_name,
        phone=phone,
        email=email,
        company=company,
        source=source,
    )

    return {"found": False, "created": True, "lead": _serialize(lead)}
