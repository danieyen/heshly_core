from __future__ import annotations

import base64

import requests

from heshly_core.services.payment.providers.mpesa_config import (
    load_mpesa_config,
)


class MpesaOAuth:

    def __init__(self):
        self.config = load_mpesa_config()

    @property
    def base_url(self) -> str:
        if self.config.environment.lower() == "production":
            return "https://api.safaricom.co.ke"
        return "https://sandbox.safaricom.co.ke"

    def get_access_token(self) -> str:
        credentials = (
            f"{self.config.consumer_key}:"
            f"{self.config.consumer_secret}"
        )

        auth = base64.b64encode(
            credentials.encode()
        ).decode()

        response = requests.get(
            f"{self.base_url}/oauth/v1/generate"
            "?grant_type=client_credentials",
            headers={
                "Authorization": f"Basic {auth}",
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()["access_token"]
