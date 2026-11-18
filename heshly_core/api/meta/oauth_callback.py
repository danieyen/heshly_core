import frappe


@frappe.whitelist(allow_guest=True)
def oauth_callback(
    code=None,
    state=None,
    error=None,
    error_description=None,
):
    """
    Meta OAuth / WhatsApp Embedded Signup callback.

    Registered callback URL:

    https://erp.heshly.com/api/method/heshly_core.api.meta.oauth_callback
    """

    if error:
        frappe.log_error(
            title="Meta Embedded Signup Error",
            message=(
                f"error={error}\n"
                f"description={error_description or ''}"
            ),
        )

        return {
            "success": False,
            "error": error,
            "error_description": error_description,
        }

    if not code:
        frappe.throw("Missing Meta authorization code")

    if not state:
        frappe.throw("Missing OAuth state")

    frappe.logger("heshly_meta").info(
        f"Meta Embedded Signup callback received. state={state}"
    )

    return {
        "success": True,
        "message": "Meta Embedded Signup callback received.",
        "state": state,
        "code_received": True,
    }
