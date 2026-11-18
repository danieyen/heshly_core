from __future__ import annotations

from heshly_core.models.payment import Payment
from heshly_core.services.payment.providers.base_provider import (
    PaymentProviderBase,
)


class MpesaProvider(PaymentProviderBase):

    def initiate_payment(self, payment: Payment):
        # TODO: Integrate Safaricom Daraja STK Push
        return {
            "success": False,
            "provider": "mpesa",
            "message": "MPesa integration not implemented.",
        }

    def verify_payment(self, provider_reference: str):
        # TODO: Query Daraja transaction status
        return {
            "verified": False,
            "provider_reference": provider_reference,
        }

    def refund(self, payment: Payment):
        # TODO: Daraja Reversal API
        return {
            "success": False,
            "provider": "mpesa",
            "message": "Refund not implemented.",
        }
