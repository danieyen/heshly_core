from __future__ import annotations

from heshly_core.models.whatsapp_number import (
    WhatsAppNumber,
)

from heshly_core.repositories.whatsapp_number_repository import (
    WhatsAppNumberRepository,
)


class WhatsAppNumberManager:
    """
    WhatsApp Number Manager.
    """

    def __init__(self):

        self.repository = (
            WhatsAppNumberRepository()
        )

    def register(
        self,
        number: WhatsAppNumber,
    ) -> WhatsAppNumber:

        if number.primary:

            for existing in self.repository.list(
                number.tenant_id
            ):

                existing.primary = False

        return self.repository.save(
            number
        )

    def numbers(
        self,
        tenant_id: str,
    ) -> list[WhatsAppNumber]:

        return self.repository.list(
            tenant_id
        )

    def primary(
        self,
        tenant_id: str,
    ) -> WhatsAppNumber | None:

        return self.repository.primary(
            tenant_id
        )

    def health(self):

        return {

            "service": "whatsapp_number_manager",

            "status": "healthy",

        }