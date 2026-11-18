from __future__ import annotations

import frappe

from heshly_core.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)


class WhatsAppConfigurationRepository:
    """
    Persistent tenant-aware WhatsApp configuration repository.

    Configuration is resolved primarily by tenant_id, but inbound
    Meta webhooks must also be resolvable by phone_number_id.
    """

    DOCTYPE = "Heshly WhatsApp Configuration"

    def save(
        self,
        configuration: WhatsAppConfiguration,
    ) -> WhatsAppConfiguration:

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "configuration_id": configuration.configuration_id,
                "tenant_id": configuration.tenant_id,
            },
            "name",
        )

        if name:
            doc = frappe.get_doc(self.DOCTYPE, name)
        else:
            doc = frappe.new_doc(self.DOCTYPE)
            doc.configuration_id = configuration.configuration_id

        doc.tenant_id = configuration.tenant_id
        doc.business_id = configuration.business_id
        doc.business_account_id = configuration.business_account_id
        doc.phone_number_id = configuration.phone_number_id
        doc.verify_token = configuration.verify_token
        doc.access_token = configuration.access_token
        doc.webhook_url = configuration.webhook_url
        doc.api_version = configuration.api_version
        doc.app_secret = configuration.app_secret
        doc.active = 1 if configuration.webhook_enabled else 0

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return configuration

    def get(
        self,
        tenant_id: str,
    ) -> WhatsAppConfiguration | None:

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "tenant_id": tenant_id,
                "active": 1,
            },
            "name",
        )

        if not name:
            return None

        return self._to_model(
            frappe.get_doc(self.DOCTYPE, name)
        )

    def get_by_phone_number_id(
        self,
        phone_number_id: str,
    ) -> WhatsAppConfiguration | None:

        if not phone_number_id:
            return None

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "phone_number_id": phone_number_id,
                "active": 1,
            },
            "name",
        )

        if not name:
            return None

        return self._to_model(
            frappe.get_doc(self.DOCTYPE, name)
        )

    def get_by_configuration_id(
        self,
        configuration_id: str,
    ) -> WhatsAppConfiguration | None:

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "configuration_id": configuration_id,
            },
            "name",
        )

        if not name:
            return None

        return self._to_model(
            frappe.get_doc(self.DOCTYPE, name)
        )

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return bool(
            frappe.db.exists(
                self.DOCTYPE,
                {
                    "tenant_id": tenant_id,
                    "active": 1,
                },
            )
        )

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "tenant_id": tenant_id,
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

    @staticmethod
    def _to_model(doc) -> WhatsAppConfiguration:

        return WhatsAppConfiguration(
            configuration_id=doc.configuration_id,
            tenant_id=doc.tenant_id,
            business_id=doc.business_id or "",
            business_account_id=doc.business_account_id or "",
            phone_number_id=doc.phone_number_id or "",
            display_phone_number=(
                doc.display_phone_number or ""
            ),
            verify_token=(
                doc.get_password("verify_token")
                if doc.verify_token
                else ""
            ),
            access_token=(
                doc.get_password("access_token")
                if doc.access_token
                else ""
            ),
            webhook_url=doc.webhook_url or "",
            language=doc.language or "en",
            api_version=doc.api_version or "v23.0",
            app_secret=(
                doc.get_password("app_secret")
                if doc.app_secret
                else ""
            ),
            webhook_enabled=bool(doc.active),
        )
