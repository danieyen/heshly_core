from __future__ import annotations

import frappe

from heshly_core.models.crm import Opportunity
from heshly_core.models.crm import OpportunityStatus
from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.repositories.opportunity_repository import OpportunityRepository


def _repository() -> OpportunityRepository:
    return OpportunityRepository()


def _serialize(opportunity: Opportunity) -> dict:
    return {
        "opportunity_id": opportunity.opportunity_id,
        "lead_id": opportunity.lead_id,
        "tenant_id": opportunity.tenant_id,
        "title": opportunity.title,
        "expected_value": opportunity.expected_value,
        "probability": opportunity.probability,
        "pipeline_id": opportunity.pipeline_id,
        "stage_id": opportunity.stage_id,
        "expected_close_date": (
            opportunity.expected_close_date.isoformat()
            if opportunity.expected_close_date
            else None
        ),
        "status": (
            opportunity.status.value
            if hasattr(opportunity.status, "value")
            else str(opportunity.status)
        ),
        "created_at": (
            opportunity.created_at.isoformat()
            if opportunity.created_at
            else None
        ),
        "updated_at": (
            opportunity.updated_at.isoformat()
            if opportunity.updated_at
            else None
        ),
    }



@frappe.whitelist()
def list_opportunities():
    opportunities = _repository().list()

    return {
        "items": [_serialize(item) for item in opportunities],
        "total": len(opportunities),
    }


@frappe.whitelist()
def get_opportunity(opportunity_id: str):
    if not opportunity_id:
        frappe.throw("opportunity_id is required")

    opportunity = _repository().get(opportunity_id)

    if not opportunity:
        frappe.throw(
            f"Opportunity '{opportunity_id}' was not found."
        )

    return _serialize(opportunity)


@frappe.whitelist()
def create_opportunity(
    lead_id: str,
    title: str,
    expected_value: float = 0,
    probability: float = 0,
    pipeline_id: str | None = None,
    stage_id: str | None = None,
    expected_close_date: str | None = None,
    status: str = "open",
):
    if not lead_id:
        frappe.throw("lead_id is required")

    if not title:
        frappe.throw("title is required")

    opportunity_id = frappe.generate_hash(
        length=12
    )

    tenant_id = TenantContext().require()

    opportunity = Opportunity(
        opportunity_id=opportunity_id,
        lead_id=lead_id,
        tenant_id=tenant_id,
        title=title,
        expected_value=float(expected_value or 0),
        probability=float(probability or 0),
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        expected_close_date=expected_close_date,
        status=OpportunityStatus(status.lower()),
    )

    saved = _repository().save(opportunity)

    return _serialize(saved)


@frappe.whitelist()
def delete_opportunity(opportunity_id: str):
    if not opportunity_id:
        frappe.throw("opportunity_id is required")

    deleted = _repository().delete(opportunity_id)

    if not deleted:
        frappe.throw(
            f"Opportunity '{opportunity_id}' was not found."
        )

    return {
        "success": True,
        "opportunity_id": opportunity_id,
    }


@frappe.whitelist()
def search_opportunities(query=None):
    query = (query or "").strip()

    if query:
        opportunities = _repository().search(query)
    else:
        opportunities = _repository().list()

    return {
        "items": [_serialize(item) for item in opportunities],
        "total": len(opportunities),
    }


@frappe.whitelist()
def get_pipeline_opportunities(pipeline_id: str):
    if not pipeline_id:
        frappe.throw("pipeline_id is required")

    opportunities = _repository().find_by_pipeline(
        pipeline_id
    )

    return {
        "items": [_serialize(item) for item in opportunities],
        "total": len(opportunities),
    }


@frappe.whitelist()
def get_stage_opportunities(stage_id: str):
    if not stage_id:
        frappe.throw("stage_id is required")

    opportunities = _repository().find_by_stage(
        stage_id
    )

    return {
        "items": [_serialize(item) for item in opportunities],
        "total": len(opportunities),
    }


@frappe.whitelist()
def get_opportunity_totals():
    repository = _repository()

    return {
        "total": repository.count(),
        "expected_value": repository.total_expected_value(),
        "weighted_value": repository.total_weighted_value(),
    }
