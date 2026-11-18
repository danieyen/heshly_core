from __future__ import annotations

import frappe

from heshly_core.services.payment.providers.mpesa_callback_parser import (
    MpesaCallbackParser,
)


@frappe.whitelist(allow_guest=True)
def callback():
    payload = frappe.request.get_json()

    result = MpesaCallbackParser.parse(payload)

    frappe.logger().info(
        {
            "mpesa_callback": result,
        }
    )

    return {
        "ResultCode": 0,
        "ResultDesc": "Accepted",
    }
