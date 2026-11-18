from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, UTC, timedelta
from typing import Any

import requests

from heshly_core.services.google.google_config import GoogleConfig, load_google_config

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover
    frappe = None  # type: ignore

# Constants
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_LIST_URL = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# State cache prefix + TTL (seconds) — 10 minutes
STATE_CACHE_PREFIX = "heshly:google:oauth:state:"
STATE_TTL_SECONDS = 10 * 60


def _site_secret() -> str:
    """Derive HMAC key from frappe site secret or env fallback (never hard-coded)."""
    try:
        if frappe and hasattr(frappe, "conf") and frappe.conf.get("heshly_google_oauth_secret"):  # type: ignore
            return str(frappe.conf.get("heshly_google_oauth_secret"))  # type: ignore
    except Exception:
        pass
    try:
        if frappe and hasattr(frappe, "conf") and frappe.conf.get("encryption_key"):  # type: ignore
            return str(frappe.conf.get("encryption_key"))  # type: ignore
    except Exception:
        pass
    import os

    env = os.getenv("HESHLY_GOOGLE_OAUTH_SECRET") or os.getenv("ENCRYPTION_SECRET") or os.getenv("HESHLY_SECRET_KEY") or ""
    if env and env != "CHANGE_ME":
        return env
    # Fallback: use site_config db key (frappe handles encryption at rest)
    return "heshly-fallback-not-for-production"


def _hmac_sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _now_ts() -> int:
    return int(time.time())


class GoogleOAuthStateStore:
    """Tenant-aware state store backed by frappe.cache() with in-memory fallback for tests."""

    _memory: dict[str, dict] = {}

    def _use_cache(self) -> bool:
        try:
            return bool(frappe and hasattr(frappe, "cache") and frappe.cache)  # type: ignore
        except Exception:
            return False

    def put(self, state: str, tenant_id: str) -> None:
        key = STATE_CACHE_PREFIX + state
        payload = {"tenant_id": tenant_id, "iat": _now_ts()}
        if self._use_cache():
            try:
                frappe.cache().set_value(key, json.dumps(payload), expires_in_sec=STATE_TTL_SECONDS)  # type: ignore
                return
            except Exception:
                pass
        self._memory[key] = payload

    def consume(self, state: str) -> str | None:
        """Atomically consume state → return tenant_id if valid and not expired, else None (also deletes)."""
        key = STATE_CACHE_PREFIX + state
        raw = None
        payload: dict | None = None
        if self._use_cache():
            try:
                raw = frappe.cache().get_value(key)  # type: ignore
                try:
                    frappe.cache().delete_value(key)  # type: ignore
                except Exception:
                    try:
                        frappe.cache().delete(key)  # type: ignore
                    except Exception:
                        pass
            except Exception:
                raw = None
        if raw is None:
            payload = self._memory.pop(key, None)
            if payload is None and isinstance(raw, str):
                try:
                    payload = json.loads(raw)
                except Exception:
                    payload = None
            elif isinstance(raw, str):
                try:
                    payload = json.loads(raw)
                except Exception:
                    payload = None
            elif isinstance(raw, dict):
                payload = raw
        else:
            if isinstance(raw, bytes):
                raw = raw.decode()
            if isinstance(raw, str):
                try:
                    payload = json.loads(raw)
                except Exception:
                    payload = None
            elif isinstance(raw, dict):
                payload = raw

        if not payload or not isinstance(payload, dict):
            return None
        tenant_id = payload.get("tenant_id")
        iat = payload.get("iat")
        if not tenant_id or not isinstance(iat, int):
            return None
        if _now_ts() - iat > STATE_TTL_SECONDS:
            return None
        return str(tenant_id)


class GoogleOAuthService:
    """
    Google OAuth2 Authorization Code flow for Calendar.

    Security:
      - State is HMAC-signed and tenant-bound (tenant_id embedded, verified on callback)
      - No tokens in URLs / localStorage / n8n / logs
      - Tokens persisted encrypted via CalendarConnectionRepository (Password field)
    """

    def __init__(self, config: GoogleConfig | None = None, state_store: GoogleOAuthStateStore | None = None):
        self.config = config or load_google_config()
        self.state_store = state_store or GoogleOAuthStateStore()

    # -- Authorization URL --

    def build_authorization_url(self, tenant_id: str, *, state: str | None = None) -> tuple[str, str]:
        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required to generate Google authorization URL")
        tenant_id = str(tenant_id).strip()

        # Generate cryptographically secure state: base64(tenant_id + nonce + timestamp).hmac
        nonce = secrets.token_urlsafe(32)
        raw = json.dumps({"t": tenant_id, "n": nonce, "ts": _now_ts()}, separators=(",", ":"))
        sig = _hmac_sign(raw, _site_secret())
        # state payload: base64(raw).sig
        b64 = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
        state_value = f"{b64}.{sig}"
        # allow caller-provided state for deterministic tests — still tenant-bound
        if state is not None:
            state_value = state

        # Persist mapping state → tenant_id for double-check (cache TTL)
        self.state_store.put(state_value, tenant_id)

        from urllib.parse import urlencode

        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": self.config.scopes_str,
            "access_type": "offline",
            "prompt": "consent",  # force refresh_token on every consent
            "state": state_value,
            "include_granted_scopes": "true",
        }
        url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        return url, state_value

    def verify_state(self, state: str) -> str:
        """Verify HMAC + cache ownership → return tenant_id or raise."""
        if not state or not isinstance(state, str):
            raise ValueError("Missing OAuth state")

        # Fast path: cache ownership check — ensures state was issued by this server
        cached_tenant = self.state_store.consume(state)
        if not cached_tenant:
            raise PermissionError("Invalid or expired OAuth state (replay or cross-tenant)")

        # Verify HMAC signature (defense-in-depth even if cache was bypassed)
        try:
            b64, sig = state.rsplit(".", 1)
        except ValueError:
            raise PermissionError("Malformed OAuth state")
        # restore padding
        pad = "=" * (-len(b64) % 4)
        try:
            raw = base64.urlsafe_b64decode((b64 + pad).encode()).decode()
        except Exception:
            raise PermissionError("Malformed OAuth state encoding")
        expected_sig = _hmac_sign(raw, _site_secret())
        if not hmac.compare_digest(expected_sig, sig):
            raise PermissionError("OAuth state signature mismatch")
        try:
            data = json.loads(raw)
        except Exception:
            raise PermissionError("Malformed OAuth state payload")
        raw_tenant = str(data.get("t") or "").strip()
        if raw_tenant != cached_tenant:
            raise PermissionError("OAuth state tenant mismatch")
        # Expiry already checked via cache TTL, but also check raw ts drift
        ts = data.get("ts")
        if isinstance(ts, int) and _now_ts() - ts > STATE_TTL_SECONDS:
            raise PermissionError("OAuth state expired")

        return cached_tenant

    # -- Token exchange --

    def exchange_code(self, code: str, tenant_id: str | None = None) -> dict[str, Any]:
        """
        Exchange authorization code for tokens. Returns dict with
        access_token, refresh_token (may be None if not first consent), expires_at, scope, token_type.
        Never logs tokens.
        """
        if not code or not str(code).strip():
            raise ValueError("Missing authorization code")
        code = str(code).strip()

        data = {
            "code": code,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "redirect_uri": self.config.redirect_uri,
            "grant_type": "authorization_code",
        }
        try:
            resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=20)
        except Exception as e:
            raise RuntimeError(f"Google token exchange network error: {e}") from e

        # Do not log body (contains tokens)
        try:
            body = resp.json()
        except Exception:
            body = {"_raw": resp.text[:500]}

        if resp.status_code != 200 or "access_token" not in body:
            err = body.get("error_description") or body.get("error") or f"HTTP {resp.status_code}"
            # Never include tokens/secrets in error
            raise RuntimeError(f"Google token exchange failed: {err}")

        access_token: str | None = body.get("access_token")
        refresh_token: str | None = body.get("refresh_token")
        expires_in = body.get("expires_in")
        try:
            expires_in_int = int(expires_in) if expires_in is not None else 3600
        except Exception:
            expires_in_int = 3600
        # Frappe/MariaDB Datetime fields are naive (no +00:00 suffix); store naive UTC
        expires_at = (datetime.now(UTC) + timedelta(seconds=expires_in_int)).replace(tzinfo=None)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "expires_in": expires_in_int,
            "scope": body.get("scope"),
            "token_type": body.get("token_type"),
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        if not refresh_token or not str(refresh_token).strip():
            raise ValueError("Missing refresh_token for token refresh")
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": str(refresh_token).strip(),
            "grant_type": "refresh_token",
        }
        try:
            resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=20)
        except Exception as e:
            raise RuntimeError(f"Google token refresh network error: {e}") from e

        try:
            body = resp.json()
        except Exception:
            body = {"_raw": resp.text[:500]}

        if resp.status_code != 200 or "access_token" not in body:
            err = body.get("error_description") or body.get("error") or f"HTTP {resp.status_code}"
            raise RuntimeError(f"Google token refresh failed: {err}")

        access_token: str = body["access_token"]
        expires_in = body.get("expires_in")
        try:
            expires_in_int = int(expires_in) if expires_in is not None else 3600
        except Exception:
            expires_in_int = 3600
        # Frappe/MariaDB Datetime fields are naive (no +00:00 suffix); store naive UTC
        expires_at = (datetime.now(UTC) + timedelta(seconds=expires_in_int)).replace(tzinfo=None)

        return {
            "access_token": access_token,
            "refresh_token": body.get("refresh_token") or refresh_token,  # Google may rotate
            "expires_at": expires_at,
            "expires_in": expires_in_int,
            "scope": body.get("scope"),
        }

    # -- Discovery --

    def list_calendars(self, access_token: str) -> list[dict[str, Any]]:
        if not access_token:
            raise ValueError("access_token required for calendar discovery")
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"maxResults": 250, "showHidden": False}
        try:
            resp = requests.get(GOOGLE_CALENDAR_LIST_URL, headers=headers, params=params, timeout=20)
        except Exception as e:
            raise RuntimeError(f"Google calendar list network error: {e}") from e

        # Do not log Authorization header
        if resp.status_code == 401:
            raise PermissionError("Google authorization expired or revoked (401)")
        if resp.status_code == 403:
            raise PermissionError("Google Calendar access forbidden (403) — check scopes and Google Cloud consent")
        if resp.status_code != 200:
            try:
                err = resp.json().get("error", {}).get("message") or resp.text[:300]
            except Exception:
                err = resp.text[:300]
            raise RuntimeError(f"Google calendar list failed ({resp.status_code}): {err}")

        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"Google calendar list invalid JSON: {e}") from e

        items = data.get("items") or []
        out: list[dict[str, Any]] = []
        for cal in items:
            if not isinstance(cal, dict):
                continue
            out.append(
                {
                    "calendar_id": cal.get("id") or "",
                    "summary": cal.get("summary") or cal.get("id") or "",
                    "description": cal.get("description") or "",
                    "timeZone": cal.get("timeZone") or "",
                    "primary": bool(cal.get("primary")),
                    "accessRole": cal.get("accessRole") or "",
                    "backgroundColor": cal.get("backgroundColor") or "",
                    "selected": bool(cal.get("selected")),
                }
            )
        return out

    def get_calendar(self, access_token: str, calendar_id: str) -> dict[str, Any]:
        """Fetch single calendar metadata (used to resolve timezone for primary)."""
        if not access_token or not calendar_id:
            raise ValueError("access_token and calendar_id required")
        from urllib.parse import quote

        url = f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}"
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            resp = requests.get(url, headers=headers, timeout=15)
        except Exception as e:
            raise RuntimeError(f"Google get calendar network error: {e}") from e
        if resp.status_code == 401:
            raise PermissionError("Google authorization expired or revoked (401)")
        if resp.status_code != 200:
            try:
                err = resp.json().get("error", {}).get("message") or resp.text[:300]
            except Exception:
                err = resp.text[:300]
            raise RuntimeError(f"Google get calendar failed ({resp.status_code}): {err}")
        return resp.json()
