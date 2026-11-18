from __future__ import annotations

import re
from urllib.parse import urlparse

import frappe
from frappe.auth import LoginManager
from frappe.utils.password import check_password as _check_password  # type: ignore

from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.repositories.frappe_business_repository import FrappeBusinessRepository

# ------------------------------------------------------------------
# Public login: tenant derived from hostname (Phase 1)
#
# API is centralized at erp.heshly.com, so Host is always erp.heshly.com.
# Tenant must be derived from the browser Origin / Referer, strictly
# validated, never from a browser-supplied business_id field.
# ------------------------------------------------------------------

_PLATFORMS = {"signup", "clients", "app", "erp", "n8n", "www", "api"}

_BUSINESS_REPO = FrappeBusinessRepository()


def _validated_heshly_hostname_from_url(url_value: str | None) -> str | None:
    """Strictly validate an Origin/Referer URL and return its hostname.

    Rules:
      - Must be HTTPS only.
      - Hostname must be `*.heshly.com` (case-insensitive).
      - Reserved labels (signup, clients, app, erp, n8n, www, api) rejected.
      - Bare `heshly.com` rejected.
      - First label extracted as business_id (hyphens normalized later).
      - `heshly.heshly.com` is explicitly allowed → HESHLY.
      - Hostname validated against `^[a-z0-9][a-z0-9\-]*[a-z0-9]$` (or single char).
    Returns lower-cased hostname if valid, otherwise None.
    """

    if not url_value or not str(url_value).strip():
        return None

    raw = str(url_value).strip()

    try:
        parsed = urlparse(raw)
    except Exception:
        return None

    # Origin is typically "https://bestt-bestt.heshly.com" (no path);
    # Referer may include path "/login". Both must be https.
    if parsed.scheme.lower() != "https":
        return None

    hostname = (parsed.hostname or "").strip().lower()

    if not hostname:
        return None

    if hostname in ("heshly.com", "localhost", "127.0.0.1"):
        return None

    if not hostname.endswith(".heshly.com"):
        return None

    label = hostname.split(".")[0]

    if not label:
        return None

    # Reserved platform subdomains must never be treated as tenants.
    # Note: "heshly" label is intentionally NOT reserved — heshly.heshly.com
    # is the tenant alias for business HESHLY.
    if label in _PLATFORMS:
        return None

    # Strict label validation: alphanumeric + hyphens, no leading/trailing hyphen
    # Allow single-char labels as well.
    if not re.match(r"^(?:[a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])$", label):
        return None

    return hostname


def _origin_tenant_hostname() -> str | None:
    """Return validated tenant hostname from Origin, or None.

    If Origin header is present but fails strict validation → return None
    and caller must fail closed (do NOT fall back to Referer/Host for this
    request, to avoid bypass via spoofed invalid Origin + valid Referer).
    """

    origin = frappe.get_request_header("Origin")

    # Fallback to raw headers dict when get_request_header misses (case, proxy)
    if not origin and hasattr(frappe.request, "headers"):
        try:
            origin = frappe.request.headers.get("Origin") or frappe.request.headers.get("origin")  # type: ignore
        except Exception:
            origin = None

    if origin is None:
        return None

    # Header present — even empty string means "present but invalid" per spec
    origin = str(origin).strip()

    if not origin:
        return None

    return _validated_heshly_hostname_from_url(origin)


def _referer_tenant_hostname() -> str | None:
    """Return validated tenant hostname from Referer, or None.

    Only called when Origin is unavailable. Same strict validation as Origin.
    """

    referer = frappe.get_request_header("Referer")

    if not referer and hasattr(frappe.request, "headers"):
        try:
            referer = frappe.request.headers.get("Referer") or frappe.request.headers.get("referer")  # type: ignore
        except Exception:
            referer = None

    if not referer:
        return None

    referer = str(referer).strip()

    if not referer:
        return None

    return _validated_heshly_hostname_from_url(referer)


def _resolve_tenant_business_from_host() -> dict | None:
    """Return active Business Account for current request’s tenant.

    Resolution order:
      1. TenantContext already set (e.g. by middleware / domain cache).
      2. Origin header hostname `https://{business_id}.heshly.com` → Business Account
         (primary for centralized API at erp.heshly.com).
      3. Referer header hostname (fallback ONLY when Origin absent) → same validation.
      4. Host header subdomain `<business_id>.heshly.com` → Business Account
         (legacy direct tenant subdomain calls).
    Never trusts a `business_id` supplied in the request body.
    """

    # Prefer middleware-populated context
    ctx_tenant = TenantContext().get()
    if ctx_tenant:
        business = frappe.db.get_value(
            "Business Account",
            {"tenant_id": ctx_tenant, "status": "Active"},
            [
                "name",
                "business_id",
                "business_name",
                "tenant_id",
                "domain",
                "status",
                "industry",
                "location",
                "timezone",
                "currency",
            ],
            as_dict=True,  # type: ignore
        )
        if business:
            return business

    # 2. Origin (centralized API primary path)
    origin_present = False
    try:
        origin_present = frappe.get_request_header("Origin") is not None
        if not origin_present and hasattr(frappe.request, "headers"):
            origin_present = (
                frappe.request.headers.get("Origin") is not None  # type: ignore
                or frappe.request.headers.get("origin") is not None  # type: ignore
            )
    except Exception:
        origin_present = False

    origin_host = _origin_tenant_hostname()

    if origin_present:
        # Heshly platform/admin frontend.
        # app.heshly.com is not a tenant subdomain, but it is the
        # centralized frontend for the HESHLY platform account.
        raw_origin = frappe.get_request_header("Origin")
        if not raw_origin and hasattr(frappe.request, "headers"):
            try:
                raw_origin = (
                    frappe.request.headers.get("Origin")
                    or frappe.request.headers.get("origin")
                )  # type: ignore
            except Exception:
                raw_origin = None

        try:
            parsed_origin = urlparse(str(raw_origin).strip()) if raw_origin else None
            if (
                parsed_origin
                and parsed_origin.scheme.lower() == "https"
                and (parsed_origin.hostname or "").lower() == "app.heshly.com"
            ):
                business = frappe.db.get_value(
                    "Business Account",
                    {"business_id": "HESHLY", "status": "Active"},
                    [
                        "name",
                        "business_id",
                        "business_name",
                        "tenant_id",
                        "domain",
                        "status",
                        "industry",
                        "location",
                        "timezone",
                        "currency",
                    ],
                    as_dict=True,  # type: ignore
                )
                return business
        except Exception:
            pass

        # Origin was sent by browser — must be valid, otherwise fail closed.
        if not origin_host:
            frappe.logger().error(f"login_business: invalid Origin header rejected: {frappe.get_request_header('Origin')!r}")  # type: ignore
            return None

        business_model = _BUSINESS_REPO.get_by_domain(origin_host)
        return business_model if business_model else None

    # 3. Referer fallback — ONLY when Origin was not sent at all
    referer_host = _referer_tenant_hostname()
    if referer_host:
        business_model = _BUSINESS_REPO.get_by_domain(referer_host)
        return business_model if business_model else None

    # 4. Legacy Host header path (direct tenant subdomain API calls)
    host = (getattr(frappe.request, "host", "") or "").split(":")[0].strip().lower()

    # Also try X-Forwarded-Host when behind NPM/Cloudflare
    if not host:
        host = (frappe.get_request_header("X-Forwarded-Host") or "").split(",")[0].strip().lower()

    if not host:
        return None

    # Ignore bare platform hosts
    label = host.split(".")[0] if host else ""
    # Treat bare heshly.com / localhost / IPs as non-tenant
    if host in ("heshly.com", "localhost", "127.0.0.1") or not label:
        return None

    # Do not treat known platform subdomains as tenants
    if label in _PLATFORMS:
        return None

    # Canonical Heshly tenant resolution: exact domain → Business Account.
    business_model = _BUSINESS_REPO.get_by_domain(host)
    return business_model if business_model else None


def _authenticate_exact_user(user_id: str, password: str) -> None:
    """Authenticate the exact submitted user; raises on failure.

    Uses Frappe's LoginManager with the supplied user; does NOT select
    an arbitrary owner.
    """

    # Resolve email / user name case-insensitively when an email was supplied
    user_name = user_id.strip()

    # Look up canonical User name if email supplied
    if "@" in user_name:
        canonical = frappe.db.get_value(
            "User",
            {"email": user_name.lower()},
            "name",
        )
        if canonical:
            user_name = canonical

    # Verify user exists and is enabled before attempting auth (prevents timing leaks too far)
    enabled = frappe.db.get_value("User", {"name": user_name}, "enabled")
    if enabled is None:
        # Generic failure — caller will map to same message
        raise frappe.AuthenticationError  # type: ignore

    if not enabled:
        raise frappe.AuthenticationError  # type: ignore

    login_manager = LoginManager()
    login_manager.authenticate(user=user_name, pwd=password)
    login_manager.post_login()
    # LoginManager sets frappe.session.user; persist
    frappe.local.session_obj.update(force=True)  # type: ignore


@frappe.whitelist(allow_guest=True)
def login_business(
    password: str | None = None,
    user_id: str | None = None,
    userId: str | None = None,
    email: str | None = None,
    # Legacy / deprecated — accepted via **kwargs below but not required.
    # Keeping an explicit name here ensures old clients calling {business_id,password}
    # continue to work via **kwargs rather than a positional required arg.
    business_id: str | None = None,  # noqa: ARG001
    businessId: str | None = None,  # noqa: ARG001
    **_kwargs: object,  # accept legacy keys without breaking Frappe RPC
):
    """Phase 1 tenant-aware login.

    Primary contract (tenant subdomain):
        POST { user_id, password }

    Legacy contract (backward compat for old frontend/tests):
        POST { business_id, password }
    Legacy is supported via kwargs — business_id is NOT a required
    positional parameter so `frappe.call(api.auth.login_business,
    user_id=…)` no longer raises `missing 1 required positional argument`.

    Tenant is NEVER taken from the body — it comes from hostname /
    TenantContext.  Browser-supplied business_id is ignored except for
    the legacy compat branch.

    Security: user_id/password pair is validated as-is; we never
    substitute another Owner.
    """

    # Normalise aliases (frontend may send user_id / userId / email)
    # Legacy business_id may arrive under businessId alias
    if business_id is None and businessId is not None:
        business_id = businessId  # type: ignore
    raw_user: str | None = user_id or userId or email  # type: ignore
    password = password or ""

    if not password:
        frappe.throw("Password is required.", frappe.ValidationError)  # type: ignore

    # ------------------------------------------------------------------
    # Legacy path — business_id + password (kept for compatibility)
    # ------------------------------------------------------------------
    # Only used when caller supplied NO user_id and DID supply business_id.
    # Behaviour is retained but fixed to authenticate the exact membership user
    # that actually matches the supplied credentials, not an arbitrary Owner.
    # This path is deprecated and will be removed once all clients migrate.
    # ------------------------------------------------------------------
    if not (raw_user and str(raw_user).strip()) and business_id and str(business_id).strip():
        legacy_bid = str(business_id).strip().upper()
        business = frappe.db.get_value(
            "Business Account",
            {"business_id": legacy_bid, "status": "Active"},
            [
                "name",
                "business_id",
                "business_name",
                "tenant_id",
                "domain",
                "status",
                "industry",
                "location",
                "timezone",
                "currency",
            ],
            as_dict=True,  # type: ignore
        )
        if not business:
            # Generic auth failure
            frappe.throw("Invalid User ID or password.", frappe.AuthenticationError)  # type: ignore

        # Enumerate active memberships — must authenticate an exact member
        # We attempt auth per-membership until one succeeds (preserves exact-user semantics
        # even under legacy contract).  Do not reveal which user existed.
        rows = frappe.get_all(
            "User Business Membership",
            filters={"business_id": business.business_id, "tenant_id": business.tenant_id, "active": 1},  # type: ignore
            fields=["user", "role"],
            limit=30,
        )
        if not rows:
            frappe.throw("Invalid User ID or password.", frappe.AuthenticationError)  # type: ignore

        last_exc: Exception | None = None
        for row in rows:
            try:
                _authenticate_exact_user(row.user, password)
                # Establish tenant context + session business on success
                TenantContext().set(business.tenant_id)
                frappe.session.data["heshly_business_id"] = business.business_id  # type: ignore
                frappe.local.session_obj.update(force=True)  # type: ignore
                return {
                    "authenticated": True,
                    "user": frappe.session.user,  # type: ignore
                    "role": row.role,
                    "business": {
                        "business_id": business.business_id,
                        "business_name": business.business_name,
                        "tenant_id": business.tenant_id,
                        "domain": business.domain,
                        "status": business.status,
                        "industry": business.industry,
                        "location": business.location,
                        "timezone": business.timezone,
                        "currency": business.currency,
                    },
                }
            except Exception as e:  # noqa: BLE001
                last_exc = e
                continue

        frappe.log_error(message=frappe.get_traceback(), title="Legacy login_business all members failed")  # type: ignore
        frappe.throw("Invalid User ID or password.", frappe.AuthenticationError)  # type: ignore

    # ------------------------------------------------------------------
    # Preferred tenant-aware path: User ID + Password
    # ------------------------------------------------------------------
    user_id_value = str(raw_user or "").strip()

    if not user_id_value:
        frappe.throw("User ID is required.", frappe.ValidationError)  # type: ignore

    business = _resolve_tenant_business_from_host()

    # Also allow TenantContext fallback for site-internal calls where Host header
    # carries erp.heshly.com but TenantContext was set earlier
    if not business:
        # Final fallback: tenant supplied explicitly by previous middleware for
        # Custom Domain tenant (business_repo.get_by_domain already applied)
        # Treat as auth failure rather than 500 so frontend shows generic error
        frappe.log_error(message=f"login_business: could not resolve tenant from host={getattr(frappe.request, 'host', None)!r}", title="Tenant resolution failed on login")  # type: ignore
        frappe.throw("Invalid User ID or password.", frappe.AuthenticationError)  # type: ignore

    # Ensure TenantContext is canonical (downstream permission checks rely on it)
    try:
        TenantContext().set(business.tenant_id)
    except Exception:  # noqa: BLE001
        pass

    # Membership check: exact user + exact tenant + active
    # Resolve canonical user name first
    canonical_user = user_id_value
    if "@" in user_id_value:
        mapped = frappe.db.get_value("User", {"email": user_id_value.lower().strip()}, "name")
        if mapped:
            canonical_user = mapped

    membership = frappe.db.get_value(
        "User Business Membership",
        {
            "user": canonical_user,
            "business_id": business.business_id,
            "tenant_id": business.tenant_id,
            "active": 1,
        },
        ["role", "user"],
        as_dict=True,  # type: ignore
    )

    if not membership:
        # Also try lower-cased user key variant (some DBs store lower-cased)
        membership = frappe.db.get_value(
            "User Business Membership",
            {
                "user": canonical_user.lower().strip(),
                "business_id": business.business_id,
                "tenant_id": business.tenant_id,
                "active": 1,
            },
            ["role", "user"],
            as_dict=True,  # type: ignore
        )

    if not membership:
        frappe.log_error(
            message=f"Tenant login membership miss: tenant={business.tenant_id} business={business.business_id} user={canonical_user!r}",
            title="Membership miss on login_business",
        )  # type: ignore
        frappe.throw("Invalid User ID or password.", frappe.AuthenticationError)  # type: ignore

    actual_user = membership.user or canonical_user

    # Verify user enabled
    enabled = frappe.db.get_value("User", {"name": actual_user}, "enabled")
    if enabled == 0:
        frappe.throw("Invalid User ID or password.", frappe.AuthenticationError)  # type: ignore

    # Authenticate the exact user/password
    try:
        _authenticate_exact_user(actual_user, password)
    except frappe.AuthenticationError:  # type: ignore
        raise
    except Exception as exc:  # noqa: BLE001
        frappe.log_error(message=frappe.get_traceback(), title="Exact user authentication failed")  # type: ignore
        frappe.throw("Invalid User ID or password.", frappe.AuthenticationError)  # type: ignore

    # Re-assert tenant context after LoginManager reset (it clears thread-locals in some versions)
    try:
        TenantContext().set(business.tenant_id)
    except Exception:  # noqa: BLE001
        pass

    # Bind Heshly business to session
    frappe.session.data["heshly_business_id"] = business.business_id  # type: ignore
    frappe.local.session_obj.update(force=True)  # type: ignore

    return {
        "authenticated": True,
        "user": frappe.session.user,  # type: ignore
        "role": membership.role,
        "business": {
            "business_id": business.business_id,
            "business_name": business.business_name,
            "tenant_id": business.tenant_id,
            "domain": business.domain,
            "status": business.status,
            "industry": business.industry,
            "location": business.location,
            "timezone": business.timezone,
            "currency": business.currency,
        },
    }


@frappe.whitelist()
def get_current_business():
    """
    Return the business associated with the authenticated
    Frappe session.
    """

    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw(
            "Authentication required.",
            frappe.PermissionError,
        )

    business_id = frappe.session.data.get(
        "heshly_business_id"
    )

    if not business_id:
        frappe.throw(
            "Business session not found.",
            frappe.PermissionError,
        )

    business = frappe.db.get_value(
        "Business Account",
        {
            "business_id": business_id,
            "status": "Active",
        },
        [
            "name",
            "business_id",
            "business_name",
            "tenant_id",
            "domain",
            "status",
            "industry",
            "location",
            "timezone",
            "currency",
        ],
        as_dict=True,
    )

    if not business:
        frappe.throw(
            "Business account not found.",
            frappe.DoesNotExistError,
        )

    membership = frappe.db.get_value(
        "User Business Membership",
        {
            "user": frappe.session.user,
            "business_id": business.business_id,
            "tenant_id": business.tenant_id,
            "active": 1,
        },
        [
            "role",
        ],
        as_dict=True,
    )

    if not membership:
        frappe.throw(
            "You do not have access to this business.",
            frappe.PermissionError,
        )

    return {
        "user": frappe.session.user,
        "role": membership.role,
        "business": {
            "business_id": business.business_id,
            "business_name": business.business_name,
            "tenant_id": business.tenant_id,
            "domain": business.domain,
            "status": business.status,
            "industry": business.industry,
            "location": business.location,
            "timezone": business.timezone,
            "currency": business.currency,
        },
    }
