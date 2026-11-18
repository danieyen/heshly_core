from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_request_middleware import (
    TenantRequestMiddleware,
)


_middleware = TenantRequestMiddleware()


def before_request():

    try:

        return _middleware.before_request()

    except RuntimeError:
        # Console/background jobs may not have an HTTP request.
        return None

    except ValueError as exc:

        # An HTTP request with an unknown/unresolvable tenant
        # must not continue without tenant context.
        frappe.throw(
            str(exc),
            exc=frappe.PermissionError,
        )

    except PermissionError as exc:

        # Tenant boundary violation.
        frappe.throw(
            str(exc),
            exc=frappe.PermissionError,
        )

    except Exception:

        frappe.log_error(
            frappe.get_traceback(),
            "Tenant Initialization Failed",
        )

        raise


def after_request(response=None, request=None):

    try:

        _middleware.after_request()

    except Exception:

        frappe.log_error(
            frappe.get_traceback(),
            "Tenant Cleanup Failed",
        )
