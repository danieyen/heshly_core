from __future__ import annotations

from heshly_core.models.whatsapp_number import (
    WhatsAppNumber,
)


class WhatsAppNumberRepository:

    def __init__(self):

        self._numbers: dict[
            str,
            list[WhatsAppNumber],
        ] = {}

    def save(
        self,
        number: WhatsAppNumber,
    ) -> WhatsAppNumber:

        self._numbers.setdefault(
            number.tenant_id,
            []
        ).append(number)

        return number

    def list(
        self,
        tenant_id: str,
    ) -> list[WhatsAppNumber]:

        return list(
            self._numbers.get(
                tenant_id,
                []
            )
        )

    def primary(
        self,
        tenant_id: str,
    ) -> WhatsAppNumber | None:

        for number in self.list(
            tenant_id
        ):

            if number.primary:

                return number

        return None