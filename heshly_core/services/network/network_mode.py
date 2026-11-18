"""Network mode detection — pure, no side effects."""

from __future__ import annotations

from heshly_core.models.network import NetworkMode
from heshly_core.services.network.settings_service import get_network_settings


def detect_mode(phone_number_id: str | None) -> NetworkMode:
    """Return HESHLY_NETWORK iff phone_number_id matches central number."""
    if not phone_number_id:
        return NetworkMode.CLIENT_RECEPTIONIST
    try:
        s = get_network_settings()
        if s.enabled and s.central_phone_number_id and str(phone_number_id).strip() == str(s.central_phone_number_id).strip():
            return NetworkMode.HESHLY_NETWORK
    except Exception:
        pass
    return NetworkMode.CLIENT_RECEPTIONIST
