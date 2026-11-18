from __future__ import annotations

import frappe


class UserBusinessRepository:
    """
    Maps ERPNext users to Business Accounts.

    Currently uses the owner field of the
    Business Account DocType.

    Future:
        • User Membership DocType
        • Roles
        • Multi-business users
    """

    def get_business_id(
        self,
        user: str,
    ) -> str | None:

        result = frappe.db.get_value(
            "Business Account",
            {
                "owner": user,
            },
            "business_id",
        )

        return result

    def get_tenant_id(
        self,
        user: str,
    ) -> str | None:

        result = frappe.db.get_value(
            "Business Account",
            {
                "owner": user,
            },
            "tenant_id",
        )

        return result

    def exists(
        self,
        user: str,
    ) -> bool:

        return self.get_business_id(user) is not None

    def health(self):

        return {
            "repository": "user_business_repository",
            "status": "healthy",
        }
