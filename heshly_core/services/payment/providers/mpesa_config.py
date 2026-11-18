from __future__ import annotations

from dataclasses import dataclass

import frappe


@dataclass(frozen=True)
class MpesaConfig:
    consumer_key: str
    consumer_secret: str
    shortcode: str
    passkey: str
    callback_url: str
    environment: str = "sandbox"


def load_mpesa_config() -> MpesaConfig:
    """
    Loads MPesa configuration from site_config.json.
    """

    conf = frappe.conf

    return MpesaConfig(
        consumer_key=conf.get("mpesa_consumer_key", ""),
        consumer_secret=conf.get("mpesa_consumer_secret", ""),
        shortcode=conf.get("mpesa_shortcode", ""),
        passkey=conf.get("mpesa_passkey", ""),
        callback_url=conf.get("mpesa_callback_url", ""),
        environment=conf.get("mpesa_environment", "sandbox"),
    )
