from __future__ import annotations

import os

import frappe

from heshly_core.services.infrastructure.nginx_proxy_manager import (
    NginxProxyManagerClient,
)


class CustomDomainSSLProvisioner:
    """
    Provisions a verified Custom Domain through Nginx Proxy Manager.

    Flow:
        1. Ensure proxy host exists.
        2. Ensure Let's Encrypt certificate exists.
        3. Attach certificate to proxy host.
        4. Persist NPM resource IDs.
        5. Mark SSL enabled only after successful provisioning.
    """

    FORWARD_HOST = os.environ.get(
        "NPM_FORWARD_HOST",
        "frappe_docker-frontend-1",
    )

    FORWARD_PORT = int(
        os.environ.get(
            "NPM_FORWARD_PORT",
            "8080",
        )
    )

    def __init__(self):
        self.npm = NginxProxyManagerClient()

    def provision(self, domain: str) -> dict:
        domain = self._normalize(domain)

        doc = frappe.db.get_value(
            "Custom Domain",
            {"domain": domain},
            [
                "name",
                "domain",
                "verified",
                "active",
                "ssl_enabled",
                "npm_certificate_id",
                "npm_proxy_host_id",
            ],
            as_dict=True,
        )

        if not doc:
            raise frappe.DoesNotExistError(
                f"Custom Domain '{domain}' does not exist."
            )

        if not doc.verified:
            raise PermissionError(
                "Custom domain must be verified before SSL "
                "provisioning."
            )

        if not doc.active:
            raise PermissionError(
                "Custom domain is inactive."
            )

        proxy = self._ensure_proxy_host(domain)

        certificate = self._ensure_certificate(domain)

        proxy_id = int(proxy["id"])
        certificate_id = int(certificate["id"])

        attached = self.npm.attach_certificate_to_proxy_host(
            proxy_id,
            certificate_id,
            ssl_forced=True,
        )

        self._persist(
            doc.name,
            certificate_id=certificate_id,
            proxy_host_id=proxy_id,
        )

        return {
            "status": "ssl_provisioned",
            "domain": domain,
            "npm_proxy_host_id": proxy_id,
            "npm_certificate_id": certificate_id,
            "ssl_provider": "Let's Encrypt",
            "proxy_host": attached,
        }

    def _ensure_proxy_host(
        self,
        domain: str,
    ) -> dict:

        existing = self.npm.find_proxy_host_by_domain(
            domain
        )

        if existing:
            proxy_id = int(existing["id"])

            self.npm.update_proxy_host(
                proxy_id,
                domain_names=[domain],
                forward_host=FORWARD_HOST,
                forward_port=FORWARD_PORT,
                forward_scheme="http",
                ssl_forced=False,
                block_exploits=True,
                allow_websocket_upgrade=True,
            )

            return self.npm.get_proxy_host(proxy_id)

        return self.npm.create_proxy_host(
            domain_names=[domain],
            forward_host=FORWARD_HOST,
            forward_port=FORWARD_PORT,
            forward_scheme="http",
            ssl_forced=False,
            block_exploits=True,
            allow_websocket_upgrade=True,
        )

    def _ensure_certificate(
        self,
        domain: str,
    ) -> dict:

        existing = self.npm.find_certificate_by_domain(
            domain
        )

        if existing:
            return existing

        return self.npm.create_letsencrypt_certificate(
            domain_names=[domain],
            nice_name=domain,
            dns_challenge=False,
        )

    @staticmethod
    def _persist(
        name: str,
        *,
        certificate_id: int,
        proxy_host_id: int,
    ) -> None:

        frappe.db.set_value(
            "Custom Domain",
            name,
            {
                "npm_certificate_id": certificate_id,
                "npm_proxy_host_id": proxy_host_id,
                "ssl_enabled": 1,
                "ssl_provider": "Let's Encrypt",
                "status": "Active",
                "ssl_last_error": None,
                "ssl_retry_count": 0,
                "ssl_next_retry_at": None,
            },
            update_modified=False,
        )

        frappe.db.commit()

    @staticmethod
    def _normalize(domain: str) -> str:
        domain = (
            domain
            .strip()
            .lower()
            .rstrip(".")
        )

        if not domain:
            raise ValueError(
                "Domain is required."
            )

        return domain
