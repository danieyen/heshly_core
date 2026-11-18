from __future__ import annotations

import os
from dataclasses import dataclass


# Google Calendar OAuth2 - follow site_config.json → frappe.conf → env var pattern
# Requires Google Cloud Console setup: https://console.cloud.google.com/apis/credentials
#
# Scopes (audited 2026-09-07 against https://www.googleapis.com/calendar/v3):
#   - GET /users/me/calendarList          → requires calendar.readonly OR calendar
#   - GET /calendars/{calendarId}         → requires calendar.readonly OR calendar  (used by health())
#   - GET/POST/PATCH/DELETE /calendars/{id}/events → requires calendar.events OR calendar
#
# Current code calls ALL of the above:
#   - discovery (calendarList) + health (calendars.get) + events CRUD
# So least-privilege MINIMAL set is EITHER:
#   (A) ["https://www.googleapis.com/auth/calendar"]  — single broad scope (simplest, covers all)
#   (B) ["https://www.googleapis.com/auth/calendar.readonly",
#        "https://www.googleapis.com/auth/calendar.events"] — least-privilege split
#
# Current GOOGLE_SCOPES = ["calendar", "calendar.events"] is REDUNDANT but not harmful —
# "calendar" is a superset of "calendar.events", so requesting both just shows
# "See, edit, share, and permanently delete all calendars you can access" once.
# Keeping as-is avoids a consent-screen / verification re-review before the first real
# connection test. Future hardening can switch to (B) if you want more granular consent.
#
# Do NOT reduce to calendar.events alone — that would break calendarList + health (403).

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

# Minimal readonly alternative if you later want split: ["https://www.googleapis.com/auth/calendar.readonly"]


@dataclass(frozen=True)
class GoogleConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]

    @property
    def scopes_str(self) -> str:
        return " ".join(self.scopes)


def _get_conf_value(key: str, env_key: str | None = None) -> str | None:
    """Resolve via site_config.json / common_site_config.json (frappe.conf) then env var."""
    env_key = env_key or key.upper()
    # 1) frappe.conf (site_config + common_site_config)
    try:
        import frappe  # type: ignore

        if hasattr(frappe, "conf") and frappe.conf:
            # frappe.conf is dict-like after bench init
            val = None
            try:
                val = frappe.conf.get(key)  # type: ignore
            except Exception:
                val = None
            if val:
                return str(val).strip()
            # try upper variant
            try:
                val = frappe.conf.get(env_key)  # type: ignore
            except Exception:
                val = None
            if val:
                return str(val).strip()
        # 2) frappe.get_site_config()
        try:
            sc = frappe.get_site_config() or {}  # type: ignore
            if isinstance(sc, dict):
                if key in sc and sc[key]:
                    return str(sc[key]).strip()
                if env_key in sc and sc[env_key]:
                    return str(sc[env_key]).strip()
        except Exception:
            pass
    except Exception:
        pass
    # 3) environment
    val = os.getenv(env_key) or os.getenv(key)
    if val:
        return str(val).strip()
    return None


def load_google_config() -> GoogleConfig:
    client_id = _get_conf_value("google_client_id", "GOOGLE_CLIENT_ID")
    client_secret = _get_conf_value("google_client_secret", "GOOGLE_CLIENT_SECRET")
    redirect_uri = _get_conf_value("google_redirect_uri", "GOOGLE_REDIRECT_URI")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Google OAuth not configured. Set google_client_id / google_client_secret in site_config.json (or GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET env)."
        )
    if not redirect_uri:
        # Default to Heshly callback path
        redirect_uri = "https://erp.heshly.com/api/method/heshly_core.api.google_oauth.callback"

    return GoogleConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scopes=list(GOOGLE_SCOPES),
    )
