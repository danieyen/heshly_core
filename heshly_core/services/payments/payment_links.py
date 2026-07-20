from __future__ import annotations

from heshly_core.models.payment import (
    Invoice,
)


class PaymentLinks:
    """
    Generates and validates payment links.
    """

    def generate(
        self,
        invoice: Invoice,
    ) -> str:

        return (
            f"https://payments.heshly.com/pay/"
            f"{invoice.invoice_id}"
        )

    def validate(
        self,
        link: str,
    ) -> bool:

        return link.startswith(
            "https://payments.heshly.com/pay/"
        )

    def extract_invoice_id(
        self,
        link: str,
    ) -> str:

        return link.rstrip("/").split("/")[-1]