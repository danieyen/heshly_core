from __future__ import annotations

import frappe

from heshly_core.services.custom_domain.custom_domain_service import (
    CustomDomainService,
)


@frappe.whitelist()
def verify(domain: str):
    service = CustomDomainService()

    return service.verify(
        domain=domain,
    )


@frappe.whitelist()
def enable_ssl(domain: str):
    service = CustomDomainService()

    return service.enable_ssl(
        domain=domain,
    )
