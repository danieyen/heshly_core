from __future__ import annotations


class MpesaSTK:

    def push(
        self,
        phone_number: str,
        amount: float,
        account_reference: str,
        transaction_desc: str,
    ) -> dict:

        return {
            "success": False,
            "message": "STK Push not implemented yet.",
            "phone_number": phone_number,
            "amount": amount,
            "account_reference": account_reference,
            "transaction_desc": transaction_desc,
        }
