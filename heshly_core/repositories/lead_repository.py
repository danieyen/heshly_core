from __future__ import annotations

from datetime import datetime

import frappe

from heshly_core.models.crm import (
    Lead,
    LeadStatus,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class LeadRepository(BaseRepository[Lead]):
    """
    Persistent, tenant-aware Lead Repository.

    Every operation is restricted to the active tenant.

    Model mapping:

        Lead.business_id
            ↕
        Lead.custom_heshly_tenant_id
    """

    DOCTYPE = "Lead"
    TENANT_FIELD = "custom_heshly_tenant_id"
    ID_FIELD = "custom_heshly_lead_id"

    # =====================================================
    # Tenant
    # =====================================================

    def _tenant_id(self) -> str:
        return self.current_tenant()

    def _validate_tenant(
        self,
        lead: Lead,
    ) -> str:

        tenant_id = self._tenant_id()

        if lead.business_id != tenant_id:
            raise PermissionError(
                "Lead belongs to a different tenant."
            )

        return tenant_id

    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        entity: Lead,
    ) -> Lead:

        tenant_id = self._validate_tenant(entity)

        existing_name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity.lead_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        # -------------------------------------------------
        # Existing Lead
        # -------------------------------------------------

        if existing_name:

            doc = frappe.get_doc(
                self.DOCTYPE,
                existing_name,
            )

        # -------------------------------------------------
        # New Lead
        # -------------------------------------------------

        else:

            doc = frappe.new_doc(
                self.DOCTYPE
            )


        # -------------------------------------------------
        # Heshly Identity
        # -------------------------------------------------

        doc.set(
            self.ID_FIELD,
            entity.lead_id,
        )

        # -------------------------------------------------
        # Tenant
        # -------------------------------------------------

        doc.set(
            self.TENANT_FIELD,
            tenant_id,
        )

        # -------------------------------------------------
        # Identity
        # -------------------------------------------------

        doc.lead_name = entity.full_name

        # -------------------------------------------------
        # Name
        # -------------------------------------------------

        name_parts = (
            entity.full_name.strip().split()
            if entity.full_name
            else []
        )

        doc.first_name = (
            name_parts[0]
            if name_parts
            else ""
        )

        doc.last_name = (
            " ".join(name_parts[1:])
            if len(name_parts) > 1
            else ""
        )

        # -------------------------------------------------
        # Contact
        # -------------------------------------------------

        doc.email_id = entity.email
        doc.mobile_no = entity.phone

        # -------------------------------------------------
        # Company
        # -------------------------------------------------

        doc.company_name = entity.company

        # -------------------------------------------------
        # Source
        # -------------------------------------------------
        # Heshly manages its own source values (e.g. portal,
        # whatsapp). Do not write them into ERPNext utm_source,
        # which is not available as a Source DocType here.

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        doc.status = self._status_to_frappe(
            entity.status
        )

        # -------------------------------------------------
        # Heshly Score
        # -------------------------------------------------

        doc.custom_heshly_score = entity.score

        # -------------------------------------------------
        # Assignment
        # -------------------------------------------------

        if entity.assigned_to:
            doc.lead_owner = entity.assigned_to
        else:
            doc.lead_owner = None
            doc.flags.ignore_mandatory = True

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
    ) -> Lead | None:

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            name = frappe.db.get_value(
                self.DOCTYPE,
                {
                    "name": entity_id,
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

    def list(self) -> list[Lead]:

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
                self.ID_FIELD: entity_id,
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
    # Exists
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
                    self.ID_FIELD: entity_id,
                    self.TENANT_FIELD: tenant_id,
                },
            )
        )

    # =====================================================
    # Count
    # =====================================================

    def count(self) -> int:

        return len(self.list())

    # =====================================================
    # Clear
    # =====================================================

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
    # Find By Email
    # =====================================================

    def find_by_email(
        self,
        email: str,
    ) -> Lead | None:

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "email_id": email.lower(),
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return None

        return self._to_model(
            frappe.get_doc(
                self.DOCTYPE,
                name,
            )
        )

    # =====================================================
    # Find By Phone
    # =====================================================

    def find_by_phone(
        self,
        phone: str,
    ) -> Lead | None:

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "mobile_no": phone,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return None

        return self._to_model(
            frappe.get_doc(
                self.DOCTYPE,
                name,
            )
        )

    # =====================================================
    # Find By Company
    # =====================================================

    def find_by_company(
        self,
        company: str,
    ) -> list[Lead]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "company_name": ["like", f"%{company}%"],
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
    # Find By Status
    # =====================================================

    def find_by_status(
        self,
        status: LeadStatus,
    ) -> list[Lead]:

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

    # =====================================================
    # Find By Source
    # =====================================================

    def find_by_source(
        self,
        source: str,
    ) -> list[Lead]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "utm_source": source,
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
    # Search
    # =====================================================

    def search(
        self,
        query: str,
    ) -> list[Lead]:

        tenant_id = self._tenant_id()

        query = query.strip()

        if not query:
            return []

        like_query = f"%{query}%"

        rows = frappe.db.sql(
            f"""
            SELECT name
            FROM `tab{self.DOCTYPE}`
            WHERE `{self.TENANT_FIELD}` = %s
              AND (
                    `lead_name` LIKE %s
                    OR `company_name` LIKE %s
                    OR `email_id` LIKE %s
                    OR `mobile_no` LIKE %s
                  )
            ORDER BY creation DESC
            """,
            (
                tenant_id,
                like_query,
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
    # Mapping
    # =====================================================

    def _to_model(
        self,
        doc,
    ) -> Lead:

        tenant_id = doc.get(
            self.TENANT_FIELD
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

        return Lead(
            lead_id=(
                doc.get(self.ID_FIELD)
                or doc.name
            ),
            business_id=tenant_id,
            full_name=(
                doc.get("lead_name")
                or ""
            ),
            phone=(
                doc.get("mobile_no")
                or doc.get("phone")
            ),
            email=doc.get("email_id"),
            company=(
                doc.get("company_name")
                or doc.get("company")
            ),
            source=(
                doc.get("utm_source")
                or "whatsapp"
            ),
            status=status,
            score=int(
                doc.get("custom_heshly_score")
                or 0
            ),
            assigned_to=doc.get(
                "lead_owner"
            ),
            created_at=created_at,
            updated_at=updated_at,
        )

    # =====================================================
    # Status Mapping
    # =====================================================

    @staticmethod
    def _status_to_frappe(
        status: LeadStatus | str,
    ) -> str:

        value = (
            status.value
            if isinstance(status, LeadStatus)
            else str(status)
        )

        # Map Heshly LeadStatus to valid ERPNext Lead.status (must be one of Lead/Open/Replied/Opportunity/Quotation/Lost Quotation/Interested/Converted/Do Not Contact)
        # Qualified is Opportunity in ERPNext semantics (lead ready for deal)
        mapping = {
            "new": "Lead",
            "contacted": "Open",
            "qualified": "Opportunity",
            "unqualified": "Do Not Contact",
            "converted": "Converted",
            "lost": "Lost Quotation",
        }

        return mapping.get(
            value.lower(),
            "Lead",
        )

    @staticmethod
    def _status_from_frappe(
        status: str | None,
    ) -> LeadStatus:

        mapping = {
            "Lead": LeadStatus.NEW,
            "Open": LeadStatus.CONTACTED,
            "Replied": LeadStatus.CONTACTED,
            "Opportunity": LeadStatus.QUALIFIED,
            "Quotation": LeadStatus.QUALIFIED,
            "Interested": LeadStatus.QUALIFIED,
            "Qualified": LeadStatus.QUALIFIED,  # legacy/back-compat
            "Contacted": LeadStatus.CONTACTED,  # legacy
            "Do Not Contact": LeadStatus.UNQUALIFIED,
            "Converted": LeadStatus.CONVERTED,
            "Lost": LeadStatus.LOST,
            "Lost Quotation": LeadStatus.LOST,
        }

        return mapping.get(
            status or "Lead",
            LeadStatus.NEW,
        )
