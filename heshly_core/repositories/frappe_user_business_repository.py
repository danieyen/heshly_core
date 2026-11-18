from __future__ import annotations

import frappe

from heshly_core.models.user_business_membership import (
    UserBusinessMembership,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class FrappeUserBusinessRepository:
    """
    Tenant-aware persistence for User Business Membership.

    TenantContext is the security boundary.

    FrappeTenantContextResolver intentionally queries the
    membership DocType directly during tenant resolution,
    before TenantContext exists. This repository is for normal
    application-level membership access after tenant context
    has been established.
    """

    DOCTYPE = "User Business Membership"

    ROLE_TO_FRAPPE = {
        "owner": "Owner",
        "administrator": "Administrator",
        "manager": "Manager",
        "receptionist": "Receptionist",
        "sales": "Sales",
        "support": "Support",
        "marketing": "Marketing",
        "accountant": "Accountant",
        "ai_manager": "AI Manager",
        "viewer": "Viewer",
    }

    ROLE_FROM_FRAPPE = {
        v: k
        for k, v in ROLE_TO_FRAPPE.items()
    }

    def __init__(self):
        self.context = TenantContext()

    # =====================================================
    # Tenant
    # =====================================================

    def current_tenant(self) -> str:
        tenant_id = self.context.get()

        if not tenant_id:
            raise PermissionError(
                "Active tenant context is required."
            )

        return tenant_id

    def _require_membership_tenant(
        self,
        membership: UserBusinessMembership,
    ) -> str:

        tenant_id = self.current_tenant()

        if membership.tenant_id != tenant_id:
            raise PermissionError(
                "Membership belongs to a different tenant."
            )

        return tenant_id

    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        membership: UserBusinessMembership,
    ) -> UserBusinessMembership:

        tenant_id = self._require_membership_tenant(
            membership
        )

        existing_name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "membership_id": membership.membership_id,
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

            doc.membership_id = (
                membership.membership_id
            )

        doc.user = membership.user
        doc.tenant_id = tenant_id
        doc.business_id = membership.business_id

        doc.role = self.ROLE_TO_FRAPPE.get(
            membership.role,
            "Viewer",
        )

        doc.active = (
            1 if membership.active else 0
        )

        doc.invited_by = membership.invited_by

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

        return membership

    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        membership_id: str,
    ) -> UserBusinessMembership | None:

        tenant_id = self.current_tenant()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "membership_id": membership_id,
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
    # User Memberships — Current Tenant Only
    # =====================================================

    def get_memberships(
        self,
        user: str,
    ) -> list[UserBusinessMembership]:

        tenant_id = self.current_tenant()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "user": user,
                "tenant_id": tenant_id,
                "active": 1,
            },
            pluck="name",
        )

        memberships = []

        for name in rows:

            membership = self.get(name)

            if membership:
                memberships.append(
                    membership
                )

        return memberships

    # =====================================================
    # Businesses — Current Tenant Only
    # =====================================================

    def get_businesses(
        self,
        user: str,
    ) -> list[str]:

        return [
            membership.business_id
            for membership in self.get_memberships(
                user
            )
        ]

    # =====================================================
    # Access — Current Tenant Only
    # =====================================================

    def has_access(
        self,
        user: str,
        business_id: str,
    ) -> bool:

        tenant_id = self.current_tenant()

        return bool(
            frappe.db.exists(
                self.DOCTYPE,
                {
                    "user": user,
                    "business_id": business_id,
                    "tenant_id": tenant_id,
                    "active": 1,
                },
            )
        )

    # =====================================================
    # Role — Current Tenant Only
    # =====================================================

    def get_role(
        self,
        user: str,
        business_id: str,
    ) -> str | None:

        tenant_id = self.current_tenant()

        role = frappe.db.get_value(
            self.DOCTYPE,
            {
                "user": user,
                "business_id": business_id,
                "tenant_id": tenant_id,
                "active": 1,
            },
            "role",
        )

        if not role:
            return None

        return self.ROLE_FROM_FRAPPE.get(
            role,
            "viewer",
        )

    # =====================================================
    # Conversion
    # =====================================================

    def _to_model(
        self,
        doc,
    ) -> UserBusinessMembership:

        return UserBusinessMembership(
            membership_id=doc.membership_id,
            user=doc.user,
            tenant_id=doc.tenant_id,
            business_id=doc.business_id,
            role=self.ROLE_FROM_FRAPPE.get(
                doc.role,
                "viewer",
            ),
            active=bool(doc.active),
            invited_by=doc.invited_by,
        )
