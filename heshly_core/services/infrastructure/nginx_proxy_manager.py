from __future__ import annotations

import os
from typing import Any

import requests


class NginxProxyManagerError(Exception):
    """Raised when Nginx Proxy Manager operations fail."""


class NginxProxyManagerClient:
    def __init__(
        self,
        base_url: str | None = None,
        identity: str | None = None,
        secret: str | None = None,
        timeout: int = 10,
    ):
        self.base_url = (
            base_url
            or os.environ.get("NPM_API_URL")
            or "http://npm:81/api"
        ).rstrip("/")

        self.identity = identity or os.environ.get("NPM_API_IDENTITY")
        self.secret = secret or os.environ.get("NPM_API_SECRET")
        self.timeout = timeout
        self._token: str | None = None

    def authenticate(self) -> str:
        if not self.identity or not self.secret:
            raise NginxProxyManagerError(
                "NPM credentials are not configured."
            )

        response = requests.post(
            f"{self.base_url}/tokens",
            json={
                "identity": self.identity,
                "secret": self.secret,
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise NginxProxyManagerError(
                f"NPM authentication failed: "
                f"{response.status_code} {response.text[:500]}"
            )

        data = response.json()
        token = data.get("token")

        if not token:
            raise NginxProxyManagerError(
                "NPM authentication returned no token."
            )

        self._token = token
        return token

    def _headers(self) -> dict[str, str]:
        if not self._token:
            self.authenticate()

        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        response = requests.request(
            method,
            f"{self.base_url}/{path.lstrip("/")}" ,
            headers=self._headers(),
            timeout=self.timeout,
            **kwargs,
        )

        if response.status_code == 401:
            self._token = None
            response = requests.request(
                method,
                f"{self.base_url}/{path.lstrip("/")}" ,
                headers=self._headers(),
                timeout=self.timeout,
                **kwargs,
            )

        if not response.ok:
            raise NginxProxyManagerError(
                f"NPM API request failed: "
                f"{response.status_code} {response.text[:1000]}"
            )

        return response

    def list_proxy_hosts(self) -> list[dict[str, Any]]:
        return self._request(
            "GET", "/nginx/proxy-hosts"
        ).json()

    def get_proxy_host(self, proxy_host_id: int) -> dict[str, Any]:
        return self._request(
            "GET", f"/nginx/proxy-hosts/{proxy_host_id}"
        ).json()

    def create_proxy_host(
        self,
        domain_names: list[str],
        forward_host: str,
        forward_port: int,
        *,
        forward_scheme: str = "http",
        ssl_forced: bool = True,
        block_exploits: bool = True,
        allow_websocket_upgrade: bool = True,
    ) -> dict[str, Any]:
        payload = {
            "domain_names": domain_names,
            "forward_host": forward_host,
            "forward_port": forward_port,
            "forward_scheme": forward_scheme,
            "ssl_forced": ssl_forced,
            "block_exploits": block_exploits,
            "allow_websocket_upgrade": allow_websocket_upgrade,
        }

        return self._request(
            "POST",
            "/nginx/proxy-hosts",
            json=payload,
        ).json()

    def update_proxy_host(
        self,
        proxy_host_id: int,
        **fields: Any,
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/nginx/proxy-hosts/{proxy_host_id}",
            json=fields,
        ).json()

    def delete_proxy_host(self, proxy_host_id: int) -> None:
        self._request(
            "DELETE",
            f"/nginx/proxy-hosts/{proxy_host_id}",
        )

    def list_certificates(self) -> list[dict[str, Any]]:
        return self._request(
            'GET',
            '/nginx/certificates',
        ).json()

    def get_certificate(
        self,
        certificate_id: int,
    ) -> dict[str, Any]:
        return self._request(
            'GET',
            f'/nginx/certificates/{certificate_id}',
        ).json()

    def create_letsencrypt_certificate(
        self,
        domain_names: list[str],
        *,
        nice_name: str | None = None,
        dns_challenge: bool = False,
    ) -> dict[str, Any]:
        payload = {
            'provider': 'letsencrypt',
            'domain_names': domain_names,
            'meta': {
                'dns_challenge': dns_challenge,
            },
        }

        if nice_name:
            payload['nice_name'] = nice_name

        return self._request(
            'POST',
            '/nginx/certificates',
            json=payload,
        ).json()

    def renew_certificate(
        self,
        certificate_id: int,
    ) -> dict[str, Any]:
        return self._request(
            'POST',
            f'/nginx/certificates/{certificate_id}/renew',
        ).json()

    def delete_certificate(
        self,
        certificate_id: int,
    ) -> None:
        self._request(
            'DELETE',
            f'/nginx/certificates/{certificate_id}',
        )

    def attach_certificate_to_proxy_host(
        self,
        proxy_host_id: int,
        certificate_id: int,
        *,
        ssl_forced: bool = True,
    ) -> dict[str, Any]:
        return self.update_proxy_host(
            proxy_host_id,
            certificate_id=certificate_id,
            ssl_forced=ssl_forced,
        )


    def find_proxy_host_by_domain(
        self,
        domain: str,
    ) -> dict[str, Any] | None:
        domain = domain.strip().lower().rstrip(".")

        for host in self.list_proxy_hosts():
            for name in host.get("domain_names", []):
                if name.strip().lower().rstrip(".") == domain:
                    return host

        return None

    def find_certificate_by_domain(
        self,
        domain: str,
    ) -> dict[str, Any] | None:
        domain = domain.strip().lower().rstrip(".")

        for certificate in self.list_certificates():
            for name in certificate.get("domain_names", []):
                if name.strip().lower().rstrip(".") == domain:
                    return certificate

        return None

