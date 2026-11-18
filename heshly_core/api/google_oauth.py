from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.services.google.google_oauth_service import GoogleOAuthService
from heshly_core.services.google.google_config import load_google_config
from heshly_core.services.calendar.calendar_connection_service import CalendarConnectionService
from heshly_core.models.calendar import CalendarProvider
from heshly_core.models.calendar_connection import CalendarConnectionStatus


def _require_tenant() -> str:
    return TenantContext().require()


def _sanitize_redirect_url(url: str) -> str:
    # Ensure redirect URL does not contain tokens (never log tokens)
    if not url:
        return url
    # Strip any access_token/refresh_token/code params if mistakenly appended
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    try:
        p = urlparse(url)
        qs = parse_qs(p.query)
        for k in ("access_token", "refresh_token", "code", "id_token"):
            qs.pop(k, None)
        new_qs = urlencode({k: v[0] if len(v) == 1 else v for k, v in qs.items()}, doseq=True)
        return urlunparse((p.scheme, p.netloc, p.path, p.params, new_qs, p.fragment))
    except Exception:
        return url


@frappe.whitelist(allow_guest=False)
def get_auth_url(calendar_id: str | None = None):
    """
    Authenticated endpoint: generate Google authorization URL for the current tenant.

    Requires Frappe session → TenantContext via before_request middleware.
    Never returns tokens. Stores state → tenant_id mapping server-side.
    """
    tenant_id = _require_tenant()
    svc = GoogleOAuthService()
    url, state = svc.build_authorization_url(tenant_id)
    # Optionally stash requested calendar_id in cache alongside state (server-side, not in state)
    # For calibration we just return URL; calendar choice happens after callback via list_calendars
    frappe.logger("heshly_google").info(f"Google auth URL generated for tenant={tenant_id}")  # never log tokens/state
    return {"success": True, "auth_url": _sanitize_redirect_url(url), "tenant_id": tenant_id}


@frappe.whitelist(allow_guest=True)
def callback(code: str | None = None, state: str | None = None, error: str | None = None, error_description: str | None = None):
    """
    OAuth2 callback. allow_guest=True because Google redirects unauthenticated;
    tenant is recovered securely from signed state (HMAC + cache), NOT from query tenant_id.

    Flow:
      verify state → tenant_id
      exchange code → tokens
      list calendars → pick primary/default
      persist CalendarConnection encrypted
    """
    if error:
        frappe.log_error(title="Google OAuth callback error", message=f"error={error} desc={error_description or ''}")
        frappe.throw(f"Google authorization failed: {error_description or error}", frappe.ValidationError)

    if not code:
        frappe.throw("Missing authorization code from Google", frappe.ValidationError)
    if not state:
        frappe.throw("Missing OAuth state", frappe.ValidationError)

    # Verify state → canonical tenant_id (prevents cross-tenant completion)
    oauth = GoogleOAuthService()
    try:
        tenant_id = oauth.verify_state(state)
    except PermissionError as e:
        frappe.log_error(title="Google OAuth state verification failed", message=str(e))
        frappe.throw(str(e), frappe.PermissionError)
    except ValueError as e:
        frappe.throw(str(e), frappe.ValidationError)

    # Set TenantContext for this request (callback is guest, so before_request cleared it)
    try:
        TenantContext().set(tenant_id)
    except Exception:
        pass

    # Exchange code for tokens (never logs tokens)
    try:
        token_data = oauth.exchange_code(code)
    except RuntimeError as e:
        frappe.log_error(title="Google token exchange failed", message=f"tenant={tenant_id} err={str(e)[:500]}")
        frappe.throw(str(e), frappe.ValidationError)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_at = token_data.get("expires_at")

    if not access_token:
        frappe.throw("Google did not return an access token", frappe.ValidationError)

    # Retrieve calendars to pick default (primary)
    try:
        calendars = oauth.list_calendars(access_token)
    except PermissionError as e:
        frappe.log_error(title="Google calendar list failed", message=f"tenant={tenant_id} err={str(e)[:500]}")
        frappe.throw(str(e), frappe.PermissionError)
    except RuntimeError as e:
        frappe.log_error(title="Google calendar list failed", message=f"tenant={tenant_id} err={str(e)[:500]}")
        frappe.throw(str(e), frappe.ValidationError)

    # Choose calendar: primary → first writer → first
    chosen = None
    for c in calendars:
        if c.get("primary"):
            chosen = c
            break
    if not chosen:
        for c in calendars:
            if c.get("accessRole") in ("owner", "writer"):
                chosen = c
                break
    if not chosen and calendars:
        chosen = calendars[0]

    calendar_id_value = (chosen.get("calendar_id") if chosen else None) or "primary"
    summary = (chosen.get("summary") if chosen else "") or calendar_id_value
    cal_tz = (chosen.get("timeZone") if chosen else "") or "Africa/Nairobi"

    # If no timezone on chosen, try fetching calendar metadata (best-effort)
    if not cal_tz or cal_tz == "":
        try:
            meta = oauth.get_calendar(access_token, calendar_id_value)
            cal_tz = meta.get("timeZone") or cal_tz or "Africa/Nairobi"
        except Exception:
            cal_tz = "Africa/Nairobi"

    # Persist connection — tokens encrypted via Password field
    conn_svc = CalendarConnectionService()
    connection_id = f"{tenant_id}:google:{calendar_id_value}"
    from heshly_core.models.calendar_connection import CalendarConnection

    conn = CalendarConnection(
        connection_id=connection_id,
        tenant_id=tenant_id,
        provider=CalendarProvider.GOOGLE,
        calendar_id=calendar_id_value,
        timezone=cal_tz,
        status=CalendarConnectionStatus.ACTIVE,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        business_name=summary,  # display-only
    )

    # Persist (TenantContext already set → repository enforces tenant match)
    try:
        saved = conn_svc.save(conn)
    except Exception as e:
        frappe.log_error(title="Google calendar connection save failed", message=f"tenant={tenant_id} err={str(e)[:500]}")
        frappe.throw(f"Failed to save Google calendar connection: {str(e)[:300]}", frappe.ValidationError)

    # Do NOT return tokens to frontend; return safe calendar choices
    safe_calendars = [
        {
            "calendar_id": c.get("calendar_id"),
            "summary": c.get("summary"),
            "description": c.get("description", ""),
            "timeZone": c.get("timeZone", ""),
            "primary": bool(c.get("primary")),
            "accessRole": c.get("accessRole", ""),
            "selected": c.get("calendar_id") == calendar_id_value,
        }
        for c in calendars
    ]

    frappe.logger("heshly_google").info(f"Google OAuth completed tenant={tenant_id} calendar={calendar_id_value}")

    # If this callback was reached via a browser redirect (Google OAuth),
    # redirect the user back to their tenant's Settings → Calendar instead
    # of stranding them on a JSON response page. API callers (bench execute,
    # curl with Accept: application/json) still get JSON.
    try:
        accept = ""
        try:
            accept = (frappe.get_request_header("Accept") or "") if hasattr(frappe, "get_request_header") else ""
        except Exception:
            accept = ""
        # Browser navigations send text/html; API clients send application/json
        wants_html = "text/html" in accept
        # Also detect if the request came from a browser navigation (no XHR header)
        is_browser_nav = wants_html
        if is_browser_nav:
            # Resolve the tenant's client domain: Business Account → domain
            # Fallback to heshly.com settings as safe default.
            target_host = None
            try:
                biz = frappe.db.get_value("Business Account", {"tenant_id": tenant_id}, "domain")
                if biz and isinstance(biz, str) and biz.strip():
                    target_host = biz.strip().lower()
                    # Business Account stores normalized domain like test-test1.heshly.com
                    if "." not in target_host:
                        target_host = None
                # Validate it looks like a heshly.com host; otherwise don't redirect there
                if target_host and not target_host.endswith(".heshly.com"):
                    target_host = None
            except Exception:
                target_host = None
            if target_host:
                redirect_url = f"https://{target_host}/settings?tab=calendar&google_connected=1"
            else:
                # Fallback: stay on current host's settings (e.g. erp.heshly.com not ideal but safe)
                redirect_url = "/settings?tab=calendar&google_connected=1"
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = redirect_url
            return None  # type: ignore
    except Exception:
        pass

    return {
        "success": True,
        "tenant_id": tenant_id,
        "connection_id": saved.connection_id,
        "calendar_id": saved.calendar_id,
        "timezone": saved.timezone,
        "status": saved.status.value if hasattr(saved.status, "value") else str(saved.status),
        "calendars": safe_calendars,
        "message": f"Google Calendar connected: {summary}",
    }


@frappe.whitelist(allow_guest=False)
def list_calendars():
    """
    Authenticated: return calendar choices for current tenant using stored access token (refresh if needed).
    Never exposes tokens.
    """
    tenant_id = _require_tenant()
    from heshly_core.services.google.google_calendar_token_service import get_valid_access_token

    try:
        access_token, connection = get_valid_access_token(tenant_id)
    except RuntimeError as e:
        frappe.throw(str(e), frappe.ValidationError)
    except PermissionError as e:
        frappe.throw(str(e), frappe.PermissionError)

    oauth = GoogleOAuthService()
    try:
        calendars = oauth.list_calendars(access_token)
    except PermissionError as e:
        frappe.throw(str(e), frappe.PermissionError)
    except RuntimeError as e:
        frappe.throw(str(e), frappe.ValidationError)

    # Mark selected (persisted calendar_id)
    selected_id = connection.calendar_id if connection else "primary"
    safe = [
        {
            "calendar_id": c.get("calendar_id"),
            "summary": c.get("summary"),
            "description": c.get("description", ""),
            "timeZone": c.get("timeZone", ""),
            "primary": bool(c.get("primary")),
            "accessRole": c.get("accessRole", ""),
            "selected": c.get("calendar_id") == selected_id,
        }
        for c in calendars
    ]
    return {"success": True, "tenant_id": tenant_id, "calendars": safe, "selected_calendar_id": selected_id}


@frappe.whitelist(allow_guest=False)
def select_calendar(calendar_id: str | None = None):
    """
    Switch the persisted calendar_id for this tenant's Google connection (e.g. user picks from list).
    Requires calendar_id ∈ calendars accessible via current token (validated server-side).
    """
    tenant_id = _require_tenant()
    if not calendar_id or not str(calendar_id).strip():
        frappe.throw("calendar_id is required", frappe.ValidationError)
    calendar_id = str(calendar_id).strip()

    from heshly_core.services.google.google_calendar_token_service import get_valid_access_token

    try:
        access_token, connection = get_valid_access_token(tenant_id)
    except RuntimeError as e:
        frappe.throw(str(e), frappe.ValidationError)

    oauth = GoogleOAuthService()
    try:
        calendars = oauth.list_calendars(access_token)
    except Exception as e:
        frappe.throw(str(e), frappe.ValidationError)

    # Validate requested calendar_id is among accessible calendars
    match = next((c for c in calendars if c.get("calendar_id") == calendar_id), None)
    if not match:
        frappe.throw(f"Calendar '{calendar_id}' not accessible for this Google account", frappe.PermissionError)

    # Persist new selection (keep tokens)
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository

    repo = CalendarConnectionRepository()
    # Find existing Google connection for this tenant
    existing = repo.get_for_provider(CalendarProvider.GOOGLE, tenant_id=tenant_id)
    if not existing:
        frappe.throw("No Google calendar connection found for this tenant. Connect Google first.", frappe.ValidationError)

    cal_tz = match.get("timeZone") or existing.timezone or "Africa/Nairobi"
    if not cal_tz:
        try:
            meta = oauth.get_calendar(access_token, calendar_id)
            cal_tz = meta.get("timeZone") or cal_tz
        except Exception:
            pass

    # If calendar_id changes we need new connection_id (tenant:google:calendar_id)
    new_connection_id = f"{tenant_id}:google:{calendar_id}"
    # Copy tokens to new connection_id if changed; delete old if different
    if existing.connection_id != new_connection_id:
        from heshly_core.models.calendar_connection import CalendarConnection

        new_conn = CalendarConnection(
            connection_id=new_connection_id,
            tenant_id=tenant_id,
            provider=CalendarProvider.GOOGLE,
            calendar_id=calendar_id,
            timezone=cal_tz,
            status=existing.status,
            access_token=existing.access_token,
            refresh_token=existing.refresh_token,
            expires_at=existing.expires_at,
            connected_at=existing.connected_at,
            business_name=match.get("summary") or "",
        )
        svc = CalendarConnectionService()
        saved = svc.save(new_conn)
        # Clean up old connection_id (best-effort, tenant-scoped)
        try:
            repo.delete(existing.connection_id, tenant_id=tenant_id)
        except Exception:
            pass
        return {"success": True, "connection_id": saved.connection_id, "calendar_id": saved.calendar_id, "timezone": saved.timezone}
    else:
        existing.calendar_id = calendar_id
        existing.timezone = cal_tz
        existing.business_name = match.get("summary") or existing.business_name
        svc = CalendarConnectionService()
        saved = svc.save(existing)
        return {"success": True, "connection_id": saved.connection_id, "calendar_id": saved.calendar_id, "timezone": saved.timezone}


@frappe.whitelist(allow_guest=False)
def disconnect():
    tenant_id = _require_tenant()
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository

    repo = CalendarConnectionRepository()
    # Delete all Google connections for this tenant (there is typically 1; support multiples if existed)
    connections = [c for c in repo.list(tenant_id=tenant_id) if c.provider == CalendarProvider.GOOGLE]
    deleted = 0
    for c in connections:
        try:
            if repo.delete(c.connection_id, tenant_id=tenant_id):
                deleted += 1
        except Exception:
            pass
    frappe.logger("heshly_google").info(f"Google disconnect tenant={tenant_id} deleted={deleted}")
    return {"success": True, "deleted": deleted}


@frappe.whitelist(allow_guest=False)
def status():
    tenant_id = _require_tenant()
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository

    repo = CalendarConnectionRepository()
    conn = repo.get_for_provider(CalendarProvider.GOOGLE, tenant_id=tenant_id)
    if not conn:
        return {"success": True, "connected": False, "tenant_id": tenant_id}
    return {
        "success": True,
        "connected": conn.status.value == "active" if hasattr(conn.status, "value") else str(conn.status) == "active",
        "tenant_id": tenant_id,
        "connection_id": conn.connection_id,
        "calendar_id": conn.calendar_id,
        "timezone": conn.timezone,
        "status": conn.status.value if hasattr(conn.status, "value") else str(conn.status),
        "expires_at": conn.expires_at.isoformat() if conn.expires_at else None,
        "has_access_token": bool(conn.access_token),
        "has_refresh_token": bool(conn.refresh_token),
        "business_name": conn.business_name or "",
    }
