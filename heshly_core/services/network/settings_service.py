"""Network settings — cached Single read. No tenant mutation."""

from __future__ import annotations

import time
from typing import Any

from heshly_core.models.network import NetworkSettings

_cache: dict[str, Any] = {"ts": 0.0, "value": None}
_TTL = 60.0


def _doc_to_settings(doc: Any) -> NetworkSettings:
    return NetworkSettings(
        enabled=bool(getattr(doc, "enabled", 0)),
        central_phone_number=getattr(doc, "central_phone_number", None) or None,
        central_phone_number_id=getattr(doc, "central_phone_number_id", None) or None,
        central_waba_id=getattr(doc, "central_waba_id", None) or None,
        central_configuration_id=getattr(doc, "central_configuration_id", None) or None,
        dispatch_timeout_seconds=int(getattr(doc, "dispatch_timeout_seconds", 300) or 300),
        max_dispatch_attempts=int(getattr(doc, "max_dispatch_attempts", 5) or 5),
        default_lead_fee=float(getattr(doc, "default_lead_fee", 0) or 0),
        currency=(getattr(doc, "currency", "KES") or "KES"),
        notify_channel=(getattr(doc, "notify_channel", "whatsapp") or "whatsapp"),
        central_display_name=getattr(doc, "central_display_name", None) or None,
        fallback_message=getattr(doc, "fallback_message", None) or None,
    )


def get_network_settings(*, force_refresh: bool = False) -> NetworkSettings:
    now = time.monotonic()
    if not force_refresh and _cache["value"] is not None and (now - float(_cache["ts"])) < _TTL:
        return _cache["value"]  # type: ignore[return-value]
    try:
        import frappe  # type: ignore
        doc = frappe.get_single("Heshly Network Settings")
        val = _doc_to_settings(doc)
    except Exception:
        val = NetworkSettings()
    _cache["ts"] = now
    _cache["value"] = val
    return val


def is_network_enabled() -> bool:
    return bool(get_network_settings().enabled and get_network_settings().central_phone_number_id)


def clear_cache() -> None:
    _cache["ts"] = 0.0
    _cache["value"] = None
