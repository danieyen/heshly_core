from __future__ import annotations


class MpesaCallbackParser:
    """
    Parses an MPesa STK callback payload into
    a simple dictionary.
    """

    @staticmethod
    def parse(payload: dict) -> dict:
        body = (
            payload.get("Body", {})
            .get("stkCallback", {})
        )

        metadata = {}

        for item in body.get("CallbackMetadata", {}).get("Item", []):
            metadata[item["Name"]] = item.get("Value")

        return {
            "merchant_request_id": body.get("MerchantRequestID"),
            "checkout_request_id": body.get("CheckoutRequestID"),
            "result_code": body.get("ResultCode"),
            "result_desc": body.get("ResultDesc"),
            "receipt_number": metadata.get("MpesaReceiptNumber"),
            "amount": metadata.get("Amount"),
            "phone_number": metadata.get("PhoneNumber"),
            "transaction_date": metadata.get("TransactionDate"),
        }
