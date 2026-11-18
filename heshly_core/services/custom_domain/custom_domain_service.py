from __future__ import annotations

from heshly_core.repositories.frappe_custom_domain_repository import (
    FrappeCustomDomainRepository,
)
from heshly_core.services.domain.dns_resolver import DNSResolver


class CustomDomainService:

    def __init__(self):
        self.repo = FrappeCustomDomainRepository()
        self.dns = DNSResolver()

    # =====================================================
    # Verify Domain
    # =====================================================

    def verify(
        self,
        domain: str,
    ):

        doc = self.repo.get(domain)

        if not doc:
            raise ValueError(
                f"Custom domain '{domain}' is not registered."
            )

        if not doc.active:
            raise PermissionError(
                "Custom domain is inactive."
            )

        if doc.verified:
            return {
                "status": "verified",
                "domain": doc.domain,
                "already_verified": True,
            }

        verified = self.dns.verify_txt(
            domain=doc.domain,
            expected_token=doc.verification_token,
        )

        if not verified:
            self.repo.mark_verification_failed(
                doc.domain
            )

            return {
                "status": "failed",
                "domain": doc.domain,
                "verified": False,
                "reason": "DNS TXT verification record not found.",
            }

        self.repo.verify(doc.domain)

        return {
            "status": "verified",
            "domain": doc.domain,
            "verified": True,
        }

    # =====================================================
    # Enable SSL
    # =====================================================

    def enable_ssl(
        self,
        domain: str,
    ):

        from heshly_core.services.custom_domain.ssl_provisioner import (
            CustomDomainSSLProvisioner,
        )

        provisioner = CustomDomainSSLProvisioner()

        return provisioner.provision(domain)
