from __future__ import annotations

import frappe


class UserProvisioningService:
    """
    Creates and manages Heshly tenant users.
    """

    def create_user(
        self,
        email: str,
        first_name: str | None = None,
        password: str | None = None,
    ) -> str:

        email = (email or "").strip().lower()

        if not email:
            raise ValueError("Email is required.")

        if frappe.db.exists("User", email):
            raise ValueError(
                "User already exists."
            )

        if not password:
            raise ValueError(
                "Password is required when creating a user."
            )

        user = frappe.new_doc("User")

        user.email = email
        user.first_name = (
            first_name
            or email.split("@")[0]
        )
        user.enabled = 1
        user.send_welcome_email = 0
        user.new_password = password

        user.save(ignore_permissions=True)

        frappe.db.commit()

        return user.name

    def health(self):
        return {
            "service": "user_provisioning_service",
            "status": "healthy",
        }
