from __future__ import annotations

import re

import frappe

from heshly_core.models.business_account import (
    BusinessAccount,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)

SHARED_PORTAL_DOMAIN = "clients.heshly.com"


def _normalize_domain(business_id: str) -> str:
    raw = str(business_id).strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    if not slug:
        raise ValueError("business_id does not contain valid characters")
    return f"{slug}.heshly.com"


class FrappeBusinessRepository(
    BaseRepository[BusinessAccount]
):
    """
    Persistent Business Account repository.

    Business Account is scoped to the canonical
    tenant_id stored in TenantContext.
    """

    DOCTYPE = "Business Account"

    STATUS_TO_FRAPPE = {
        "active": "Active",
        "inactive": "Inactive",
        "suspended": "Suspended",
    }

    STATUS_FROM_FRAPPE = {
        "Active": "active",
        "Inactive": "inactive",
        "Suspended": "suspended",
    }

    # =====================================================
    # Tenant Validation
    # =====================================================

    def _require_business_tenant(
        self,
        business: BusinessAccount,
    ) -> str:

        tenant_id = self.current_tenant()

        if business.tenant_id != tenant_id:
            raise PermissionError(
                "Business belongs to a different tenant."
            )

        return tenant_id

    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        business: BusinessAccount,
    ) -> BusinessAccount:

        tenant_id = self._require_business_tenant(
            business
        )

        existing_name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "business_id": business.business_id,
                "tenant_id": tenant_id,
            },
            "name",
        )

        if existing_name:
            doc = frappe.get_doc(
                self.DOCTYPE,
                existing_name,
            )
        else:
            doc = frappe.new_doc(
                self.DOCTYPE
            )

            doc.business_id = business.business_id

        doc.business_name = business.name
        doc.tenant_id = tenant_id
        # Server-controlled domain invariant: always normalize from business_id.
        # Never trust business.domain if it is clients.heshly.com or malformed.
        _expected = _normalize_domain(business.business_id)
        supplied = (business.domain or "").strip().lower()
        if supplied == SHARED_PORTAL_DOMAIN or supplied != _expected.lower():
            # Enforce server ownership; log override for audit
            if supplied == SHARED_PORTAL_DOMAIN:
                frappe.logger().warning(
                    f"FrappeBusinessRepository.save: rejected shared portal domain for {business.business_id}"
                )
            business.domain = _expected
        doc.domain = business.domain
        doc.email = business.email
        doc.phone = business.phone

        doc.status = self.STATUS_TO_FRAPPE.get(
            business.status,
            "Active",
        )

        doc.industry = business.profile.industry
        doc.location = business.profile.location

        doc.timezone = business.settings.timezone
        doc.currency = business.settings.currency

        if existing_name:
            doc.save(
                ignore_permissions=True
            )
        else:
            doc.insert(
                ignore_permissions=True,
                ignore_links=True,
            )

        frappe.db.commit()

        return business

         # =====================================================
    # Resolve Tenant From Domain
    # =====================================================

    def get_by_domain(
        self,
        domain: str | None = None,
    ) -> BusinessAccount | None:

        if not domain:
            return None

        domain = (
            domain
            .lower()
            .strip()
            .rstrip(".")
        )

        # -------------------------------------------------
        # 1. Primary Business Account domain / tenant subdomain
        # -------------------------------------------------
        #
        # Tenant login contract:  {business_id}.heshly.com  →  business_id
        # The Business Account’s `domain` is intentionally NOT the tenant
        # subdomain — every tenant today has domain=clients.heshly.com.
        # For tenant requests we therefore probe the subdomain as a
        # business_id when the literal domain lookup fails.
        #
        # This probe is case-insensitive, ordered after the literal
        # domain match, and never trusts an arbitrary header — it queries
        # the canonical Business Account row.
        #

        row = frappe.db.get_value(
            self.DOCTYPE,
            {
                "domain": domain,
                "status": "Active",
            },
            [
                "name",
                "business_id",
                "business_name",
                "tenant_id",
                "domain",
                "email",
                "phone",
                "status",
                "industry",
                "location",
                "timezone",
                "currency",
            ],
            as_dict=True,
        )

        if row:
            return self._row_to_model(row)

        # Tenant subdomain fallback — e.g. kimpo_hgvyvw.heshly.com or two-names-two.heshly.com
        # Requirement: business name is the business ID; multi-word names use hyphens
        # in the subdomain (two names → two-names.heshly.com).  Stored business_id
        # is underscore form (two_names_two) — subdomain may arrive hyphenated.
        # Only for hosts ending with .heshly.com with a non-platform first label.
        # `heshly` itself is a platform host only when the literal domain is
        # `heshly.com`; the subdomain `heshly.heshly.com` (for business HESHLY)
        # is a tenant alias and must be handled via tenant_id, not domain label.
        subdomain = domain.split(".")[0] if domain.endswith(".heshly.com") and "." in domain else ""
        _is_bare_heshly = domain == "heshly.com"
        _platform_labels = {"signup", "clients", "app", "erp", "n8n", "www", "api"}
        if _is_bare_heshly:
            _platform_labels.add("heshly")
        if subdomain and subdomain.lower() not in _platform_labels:
            # Accept both hyphenated (two-names-two) and underscore (two_names_two) subdomain forms.
            sub_key = subdomain.replace("-", "_").upper()
            sub_row = frappe.db.get_value(
                self.DOCTYPE,
                {"business_id": sub_key, "status": "Active"},
                [
                    "name",
                    "business_id",
                    "business_name",
                    "tenant_id",
                    "domain",
                    "email",
                    "phone",
                    "status",
                    "industry",
                    "location",
                    "timezone",
                    "currency",
                ],
                as_dict=True,
            )
            if sub_row:
                return self._row_to_model(sub_row)

            custom_sub = frappe.db.get_value(
                "Custom Domain",
                {"domain": domain, "verified": 1, "active": 1},
                ["business_id", "tenant_id"],
                as_dict=True,
            )
            if custom_sub:
                sub_biz = frappe.db.get_value(
                    self.DOCTYPE,
                    {"business_id": custom_sub.business_id, "tenant_id": custom_sub.tenant_id, "status": "Active"},
                    [
                        "name",
                        "business_id",
                        "business_name",
                        "tenant_id",
                        "domain",
                        "email",
                        "phone",
                        "status",
                        "industry",
                        "location",
                        "timezone",
                        "currency",
                    ],
                    as_dict=True,
                )
                if sub_biz:
                    return self._row_to_model(sub_biz)

        # -------------------------------------------------
        # 2. Verified Custom Domain
        # -------------------------------------------------
        #
        # This lookup intentionally happens before
        # TenantContext exists. The request middleware calls
        # get_by_domain() specifically to establish the
        # tenant context.
        #
        # Security requirements:
        #   - custom domain must be verified
        #   - custom domain must be active
        #   - owning Business Account must be active
        #   - business_id and tenant_id must match
        #

        custom = frappe.db.get_value(
            "Custom Domain",
            {
                "domain": domain,
                "verified": 1,
                "active": 1,
            },
            [
                "business_id",
                "tenant_id",
            ],
            as_dict=True,
        )

        if not custom:
            return None

        # -------------------------------------------------
        # 3. Resolve owning Business Account
        # -------------------------------------------------

        business = frappe.db.get_value(
            self.DOCTYPE,
            {
                "business_id": custom.business_id,
                "tenant_id": custom.tenant_id,
                "status": "Active",
            },
            [
                "name",
                "business_id",
                "business_name",
                "tenant_id",
                "domain",
                "email",
                "phone",
                "status",
                "industry",
                "location",
                "timezone",
                "currency",
            ],
            as_dict=True,
        )

        if not business:
            return None

        return self._row_to_model(business)

    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        business_id: str | None = None,
    ) -> BusinessAccount | None:

        if not business_id:
            raise ValueError(
                "business_id is required."
            )

        tenant_id = self.current_tenant()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "business_id": business_id,
                "tenant_id": tenant_id,
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
    # All — Current Tenant Only
    # =====================================================

    def all(self) -> list[BusinessAccount]:

        tenant_id = self.current_tenant()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "tenant_id": tenant_id,
            },
            fields=[
                "name",
                "business_id",
                "business_name",
                "tenant_id",
                "domain",
                "email",
                "phone",
                "status",
                "industry",
                "location",
                "timezone",
                "currency",
            ],
            order_by="creation desc",
        )

        return [
            self._row_to_model(row)
            for row in rows
        ]

    # =====================================================
    # Exists
    # =====================================================

    def exists(
        self,
        business_id: str | None = None,
    ) -> bool:

        if not business_id:
            raise ValueError(
                "business_id is required."
            )

        tenant_id = self.current_tenant()

        return bool(
            frappe.db.exists(
                self.DOCTYPE,
                {
                    "business_id": business_id,
                    "tenant_id": tenant_id,
                },
            )
        )

    # =====================================================
    # Row → Model
    # =====================================================

    def _row_to_model(
        self,
        row,
    ) -> BusinessAccount:

        business = BusinessAccount(
            business_id=row.business_id,
            tenant_id=row.tenant_id,
            name=row.business_name,
            domain=row.domain,
            email=row.email,
            phone=row.phone,
            status=self.STATUS_FROM_FRAPPE.get(
                row.status,
                "active",
            ),
        )

        business.profile.industry = row.industry
        business.profile.location = row.location

        business.settings.timezone = (
            row.timezone
            or business.settings.timezone
        )

        business.settings.currency = (
            row.currency
            or business.settings.currency
        )

        return business

    # =====================================================
    # DocType → Model
    # =====================================================

    def _to_model(
        self,
        doc,
    ) -> BusinessAccount:

        business = BusinessAccount(
            business_id=doc.business_id,
            tenant_id=doc.tenant_id,
            name=doc.business_name,
            domain=doc.domain,
            email=doc.email,
            phone=doc.phone,
            status=self.STATUS_FROM_FRAPPE.get(
                doc.status,
                "active",
            ),
        )

        business.profile.industry = doc.industry
        business.profile.location = doc.location

        business.settings.timezone = (
            doc.timezone
            or business.settings.timezone
        )

        business.settings.currency = (
            doc.currency
            or business.settings.currency
        )

        return business

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {
            "repository":
                "frappe_business_repository",

            "status":
                "healthy",

            "tenant":
                self.has_tenant(),

            "records":
                frappe.db.count(
                    self.DOCTYPE
                ),
        }
