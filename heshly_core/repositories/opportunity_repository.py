from __future__ import annotations

from datetime import datetime

import frappe

from heshly_core.models.crm import (
    Opportunity,
    OpportunityStatus,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class OpportunityRepository(BaseRepository[Opportunity]):
    """
    Persistent, tenant-aware Opportunity Repository.

    Every operation is restricted to the active tenant.

    Model mapping:

        Opportunity.tenant_id
            ↕
        Opportunity.custom_heshly_tenant_id
    """

    DOCTYPE = "Opportunity"
    TENANT_FIELD = "custom_heshly_tenant_id"
    OPPORTUNITY_ID_FIELD = "custom_heshly_opportunity_id"
    LEAD_ID_FIELD = "custom_heshly_lead_id"
    PIPELINE_ID_FIELD = "custom_heshly_pipeline_id"
    STAGE_ID_FIELD = "custom_heshly_stage_id"

    # =====================================================
    # Tenant
    # =====================================================

    def _tenant_id(self) -> str:
        return self.current_tenant()

    def _validate_tenant(
        self,
        opportunity: Opportunity,
    ) -> str:
        tenant_id = self._tenant_id()

        if opportunity.tenant_id != tenant_id:
            raise PermissionError(
                "Opportunity belongs to a different tenant."
            )

        return tenant_id

    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        entity: Opportunity,
    ) -> Opportunity:

        tenant_id = self._validate_tenant(entity)

        existing_name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.OPPORTUNITY_ID_FIELD: entity.opportunity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        # -------------------------------------------------
        # Existing Opportunity
        # -------------------------------------------------

        if existing_name:
            doc = frappe.get_doc(
                self.DOCTYPE,
                existing_name,
            )

        # -------------------------------------------------
        # New Opportunity
        # -------------------------------------------------

        else:
            doc = frappe.new_doc(
                self.DOCTYPE
            )

        # -------------------------------------------------
        # Tenant
        # -------------------------------------------------

        doc.set(
            self.TENANT_FIELD,
            tenant_id,
        )

        # -------------------------------------------------
        # Heshly Identity
        # -------------------------------------------------

        doc.set(
            self.OPPORTUNITY_ID_FIELD,
            entity.opportunity_id,
        )

        doc.set(
            self.LEAD_ID_FIELD,
            entity.lead_id,
        )

        # -------------------------------------------------
        # ERPNext Lead Relationship
        # -------------------------------------------------

        doc.opportunity_from = "Lead"

        lead_name = frappe.db.get_value(
            "Lead",
            {
                "custom_heshly_lead_id": entity.lead_id,
                "custom_heshly_tenant_id": tenant_id,
            },
            "name",
        )

        if not lead_name:
            raise frappe.ValidationError(
                f"Heshly Lead '{entity.lead_id}' was not found "
                f"for tenant '{tenant_id}'."
            )

        doc.party_name = lead_name

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        doc.title = entity.title

        # -------------------------------------------------
        # Pipeline
        # -------------------------------------------------

        doc.set(
            self.PIPELINE_ID_FIELD,
            entity.pipeline_id,
        )

        # -------------------------------------------------
        # Stage
        # -------------------------------------------------

        doc.set(
            self.STAGE_ID_FIELD,
            entity.stage_id,
        )

        # -------------------------------------------------
        # Expected Close
        # -------------------------------------------------

        doc.expected_closing = entity.expected_close_date

        # -------------------------------------------------
        # Probability
        # -------------------------------------------------

        doc.probability = entity.probability * 100

        # -------------------------------------------------
        # Value
        # -------------------------------------------------

        doc.opportunity_amount = entity.expected_value

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        doc.status = self._status_to_frappe(
            entity.status
        )

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        doc.save(
            ignore_permissions=True
        )

        frappe.db.commit()

        return self._to_model(doc)

    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        entity_id: str,
    ) -> Opportunity | None:

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.OPPORTUNITY_ID_FIELD: entity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return None

        doc = frappe.get_doc(
            self.DOCTYPE,
            name,
        )

        return self._to_model(doc)

    # =====================================================
    # List
    # =====================================================

    def list(self) -> list[Opportunity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.OPPORTUNITY_ID_FIELD: entity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return False

        frappe.delete_doc(
            self.DOCTYPE,
            name,
            ignore_permissions=True,
        )

        frappe.db.commit()

        return True

    # =====================================================
    # Utilities
    # =====================================================

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        tenant_id = self._tenant_id()

        return bool(
            frappe.db.exists(
                self.DOCTYPE,
                {
                    self.OPPORTUNITY_ID_FIELD: entity_id,
                    self.TENANT_FIELD: tenant_id,
                },
            )
        )

    def count(self) -> int:
        return len(self.list())

    def clear(self) -> None:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            pluck="name",
        )

        for name in rows:
            frappe.delete_doc(
                self.DOCTYPE,
                name,
                ignore_permissions=True,
            )

        frappe.db.commit()

    # =====================================================
    # Opportunity Queries
    # =====================================================

    def find_by_lead(
        self,
        lead_id: str,
    ) -> list[Opportunity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.LEAD_ID_FIELD: lead_id,
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    def find_by_status(
        self,
        status: OpportunityStatus,
    ) -> list[Opportunity]:

        tenant_id = self._tenant_id()

        frappe_status = self._status_to_frappe(
            status
        )

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "status": frappe_status,
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    def find_by_pipeline(
        self,
        pipeline_id: str,
    ) -> list[Opportunity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.PIPELINE_ID_FIELD: pipeline_id,
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    def find_by_stage(
        self,
        stage_id: str,
    ) -> list[Opportunity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.STAGE_ID_FIELD: stage_id,
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    def search(
        self,
        query: str,
    ) -> list[Opportunity]:

        query = query.strip()

        if not query:
            return []

        tenant_id = self._tenant_id()

        like_query = f"%{query}%"

        rows = frappe.db.sql(
            f"""
            SELECT name
            FROM `tab{self.DOCTYPE}`
            WHERE `{self.TENANT_FIELD}` = %s
              AND (
                    `title` LIKE %s
                    OR `{self.PIPELINE_ID_FIELD}` LIKE %s
                    OR `{self.STAGE_ID_FIELD}` LIKE %s
                  )
            ORDER BY creation DESC
            """,
            (
                tenant_id,
                like_query,
                like_query,
                like_query,
            ),
            as_dict=True,
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    # =====================================================
    # Financial Queries
    # =====================================================

    def total_expected_value(self) -> float:

        tenant_id = self._tenant_id()

        result = frappe.db.sql(
            f"""
            SELECT COALESCE(
                SUM(`opportunity_amount`),
                0
            ) AS total
            FROM `tab{self.DOCTYPE}`
            WHERE `{self.TENANT_FIELD}` = %s
            """,
            (tenant_id,),
            as_dict=True,
        )

        return float(result[0].total or 0)

    def total_weighted_value(self) -> float:

        tenant_id = self._tenant_id()

        result = frappe.db.sql(
            f"""
            SELECT COALESCE(
                SUM(
                    `opportunity_amount`
                    * (`probability` / 100)
                ),
                0
            ) AS total
            FROM `tab{self.DOCTYPE}`
            WHERE `{self.TENANT_FIELD}` = %s
            """,
            (tenant_id,),
            as_dict=True,
        )

        return float(result[0].total or 0)

    # =====================================================
    # Mapping
    # =====================================================

    def _to_model(
        self,
        doc,
    ) -> Opportunity:

        tenant_id = doc.get(
            self.TENANT_FIELD
        )

        opportunity_id = doc.get(
            self.OPPORTUNITY_ID_FIELD
        ) or doc.name

        lead_id = doc.get(
            self.LEAD_ID_FIELD
        ) or ""

        pipeline_id = doc.get(
            self.PIPELINE_ID_FIELD
        )

        stage_id = doc.get(
            self.STAGE_ID_FIELD
        )

        status = self._status_from_frappe(
            doc.get("status")
        )

        created_at = (
            doc.get("creation")
            or datetime.utcnow()
        )

        updated_at = (
            doc.get("modified")
            or created_at
        )

        return Opportunity(
            opportunity_id=opportunity_id,
            lead_id=lead_id,
            tenant_id=tenant_id,
            title=(
                doc.get("title")
                or ""
            ),
            expected_value=float(
                doc.get("opportunity_amount")
                or 0
            ),
            probability=float(
                doc.get("probability")
                or 0
            ) / 100,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            expected_close_date=doc.get(
                "expected_closing"
            ),
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )

    # =====================================================
    # Status Mapping
    # =====================================================

    @staticmethod
    def _status_to_frappe(
        status: OpportunityStatus | str,
    ) -> str:

        value = (
            status.value
            if isinstance(status, OpportunityStatus)
            else str(status)
        )

        mapping = {
            "open": "Open",
            "won": "Converted",
            "lost": "Lost",
        }

        return mapping.get(
            value.lower(),
            "Open",
        )

    @staticmethod
    def _status_from_frappe(
        status: str | None,
    ) -> OpportunityStatus:

        mapping = {
            "Open": OpportunityStatus.OPEN,
            "Converted": OpportunityStatus.WON,
            "Lost": OpportunityStatus.LOST,
        }

        return mapping.get(
            status or "Open",
            OpportunityStatus.OPEN,
        )
