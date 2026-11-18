from __future__ import annotations

import frappe

from heshly_core.repositories.frappe_business_repository import (
    FrappeBusinessRepository,
)

from heshly_core.services.tenant.frappe_tenant_context_resolver import (
    FrappeTenantContextResolver,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.subscription.subscription_request_gate import (
    SubscriptionRequestGate,
)


class TenantRequestMiddleware:

    def __init__(self):

        self.business_repo = (
            FrappeBusinessRepository()
        )

        self.user_resolver = (
            FrappeTenantContextResolver()
        )

        self.context = TenantContext()

        self.subscription_gate = (
            SubscriptionRequestGate()
        )

    # =====================================================
    # Before Request
    # =====================================================

    def before_request(self) -> str:

        if not getattr(
            frappe,
            "request",
            None,
        ):
            raise RuntimeError(
                "No active HTTP request."
            )

        # Always begin clean.
        self.context.clear()

        # -------------------------------------------------
        # Public WhatsApp webhook
        #
        # Meta verification and webhook delivery authenticate
        # at the webhook layer, not through Frappe login or
        # tenant membership.
        # -------------------------------------------------

        request_path = frappe.request.path.rstrip("/")  # type: ignore

        # Public website — heshly.com must not require Business Account or tenant.
        # Serve static marketing site without auth/tenant checks.
        # Check Host via request.host and X-Forwarded-Host (frontend nginx preserves $host)
        _host_www = (getattr(frappe.request, "host", "") or "").split(":")[0].lower()
        try:
            _xfh = (frappe.get_request_header("X-Forwarded-Host") or "").split(",")[0].strip().lower().split(":")[0]
            if _xfh:
                _host_www = _xfh
        except Exception:
            pass
        if _host_www in ("heshly.com", "www.heshly.com"):
            if not request_path.startswith("/api/"):
                self.context.clear()
                return None  # type: ignore

        # -----------------------------------------------------------------
        # Wildcard CORS for tenant subdomains
        # site_config.json contains "https://*.heshly.com" but Frappe's
        # set_cors_headers does literal equality, so new tenants fail CORS.
        # Set frappe.local.allow_cors to the exact Origin if it matches
        # https://*.heshly.com and is not a reserved platform label, so
        # set_cors_headers emits Access-Control-Allow-Origin with credentials.
        # -----------------------------------------------------------------
        try:
            _origin = frappe.get_request_header("Origin")
            if not _origin and hasattr(frappe.request, "headers"):
                _origin = frappe.request.headers.get("Origin") or frappe.request.headers.get("origin")  # type: ignore
            if _origin and isinstance(_origin, str) and _origin.strip():
                _o = _origin.strip()
                # Must be https and *.heshly.com
                from urllib.parse import urlparse as _urlparse  # local import
                _parsed = _urlparse(_o)
                _host = (_parsed.hostname or "").lower()
                if _parsed.scheme.lower() == "https" and _host.endswith(".heshly.com"):
                    _label = _host.split(".")[0]
                    _platforms = {"signup", "clients", "app", "erp", "n8n", "www", "api"}
                    # heshly.heshly.com is explicitly allowed as tenant alias
                    if _label not in _platforms or _host == "heshly.heshly.com":
                        # Strict label validation same as auth.py
                        import re as _re
                        if _re.match(r"^(?:[a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])$", _label):
                            frappe.local.allow_cors = _o  # exact origin for credentials
        except Exception:
            pass

        # Public tenant-aware login — must NOT force Host-based tenant.
        # The API is centralized at erp.heshly.com, tenant comes from Origin/Referer.
        if request_path == "/api/method/heshly_core.api.auth.login_business":
            self.context.clear()
            return None  # type: ignore

        # Public Google OAuth callback.
        # Google redirects here without a Frappe session.
        # Tenant is established securely inside the callback from
        # the validated, signed OAuth state — never from Host/query params.
        if request_path == "/api/method/heshly_core.api.google_oauth.callback":
            self.context.clear()
            return None  # type: ignore

        # Public signup — same centralized API, no host-based tenant.
        if request_path == "/api/method/heshly_core.api.signup.signup":
            self.context.clear()
            return None  # type: ignore

        # -------------------------------------------------
        # Guest tenant resolution from Origin
        #
        # Tenant frontends use erp.heshly.com as the API host.
        # For unauthenticated tenant-origin requests, Host is
        # therefore erp.heshly.com and cannot identify the tenant.
        #
        # Resolve a valid Heshly tenant from Origin instead.
        # Authenticated requests remain session-derived below.
        # -------------------------------------------------
        try:
            _origin = frappe.get_request_header("Origin")

            if not _origin and hasattr(frappe.request, "headers"):
                _origin = (
                    frappe.request.headers.get("Origin")
                    or frappe.request.headers.get("origin")
                )

            if _origin and isinstance(_origin, str):
                from urllib.parse import urlparse as _urlparse

                _origin = _origin.strip()
                _parsed_origin = _urlparse(_origin)

                _origin_host = (
                    _parsed_origin.hostname or ""
                ).lower().strip()

                if (
                    _parsed_origin.scheme.lower() == "https"
                    and _origin_host.endswith(".heshly.com")
                    and _origin_host not in {
                        "heshly.com",
                        "www.heshly.com",
                        "signup.heshly.com",
                        "clients.heshly.com",
                        "app.heshly.com",
                        "erp.heshly.com",
                        "n8n.heshly.com",
                        "api.heshly.com",
                    }
                ):
                    _origin_business = (
                        self.business_repo.get_by_domain(
                            _origin_host
                        )
                    )

                    if _origin_business:
                        _origin_tenant = (
                            _origin_business.tenant_id
                        )

                        _origin_user = (
                            frappe.session.user
                            if hasattr(frappe, "session")
                            else None
                        )

                        # Only use Origin for guest requests.
                        if not _origin_user or _origin_user == "Guest":
                            self.context.set(_origin_tenant)
                            return _origin_tenant

        except Exception:
            pass

        # Centralized session lookup — session already carries heshly_business_id,
        # so Host check must NOT override it (Host is always erp.heshly.com).
        # Must be exempt like login_business.
        #
        # All Heshly Core frontend APIs on the centralized API host (erp.heshly.com)
        # are authenticated via session cookie; TenantContext must be derived from
        # the session's business, NOT from Host (which is always erp.heshly.com).
        # Without this, any tenant user calling analytics on erp.heshly.com would
        # be forced onto tenant heshly (Business Account HESHLY), breaking
        # tenant isolation for every secondary tenant like test_test1 and causing
        # the reported 403s + google_oauth.get_auth_url PermissionError.
        #
        # Analytics / Business Account resource are also covered here (previously
        # fell through to Host resolution → wrong tenant → 403).
        if request_path in (
            "/api/method/heshly_core.api.auth.get_current_business",
            "/api/method/heshly_core.api.whatsapp_connect.get_whatsapp_connection",
            "/api/method/heshly_core.api.whatsapp_connect.exchange_meta_code",
            "/api/method/heshly_core.api.whatsapp_connect.disconnect_whatsapp",
            "/api/method/heshly_core.api.whatsapp_connect.list_whatsapp_connections",
            "/api/method/heshly_core.api.whatsapp_connect_admin.list_whatsapp_connections",
            "/api/method/heshly_core.api.google_oauth.get_auth_url",
            "/api/method/heshly_core.api.google_oauth.list_calendars",
            "/api/method/heshly_core.api.google_oauth.select_calendar",
            "/api/method/heshly_core.api.google_oauth.disconnect",
            "/api/method/heshly_core.api.google_oauth.status",
            "/api/method/heshly_core.api.google_debug.status",
            "/api/method/heshly_core.api.google_debug.list_calendars",
            "/api/method/heshly_core.api.google_debug.health",
            "/api/method/heshly_core.api.google_debug.test_get_events",
            "/api/method/heshly_core.api.google_debug.test_create_event",
            # Analytics + Business Account resource — same centralized session pattern
            "/api/method/heshly_core.api.analytics.get_conversation_analytics",
            "/api/method/heshly_core.api.analytics.get_opportunity_analytics",
            "/api/method/heshly_core.api.analytics.get_appointment_analytics",
            "/api/method/heshly_core.api.analytics.get_lead_analytics",
            "/api/method/heshly_core.api.analytics.get_usage_analytics",
            "/api/method/heshly_core.api.analytics.get_dashboard_analytics",
            "/api/method/heshly_core.api.analytics.get_business_analytics",
            "/api/method/heshly_core.api.analytics.get_sales_analytics",
            "/api/method/heshly_core.api.analytics.get_campaign_analytics",
            "/api/method/heshly_core.api.analytics.get_whatsapp_analytics",
            "/api/method/heshly_core.api.analytics.get_reports",
            "/api/resource/Business Account",
        ) or request_path.startswith("/api/resource/Business Account"):
            # Still emit wildcard CORS above; just skip Host tenant resolution.
            # If already authenticated, populate TenantContext from session for downstream.
            try:
                _bid = frappe.session.data.get("heshly_business_id") if hasattr(frappe, "session") and hasattr(frappe.session, "data") else None  # type: ignore
                if _bid:
                    _tenant = frappe.db.get_value("Business Account", {"business_id": _bid}, "tenant_id")
                    if _tenant:
                        self.context.set(_tenant)
                        # For resource routes (/api/resource/Business Account/<id>) also skip Host
                        # resolution entirely once session tenant is established.
                        return _tenant  # type: ignore
                    # Session holds stale business_id (business deleted / renamed) —
                    # fall through to no-context so API returns 404 rather than 403
                    return None  # type: ignore
                # No heshly_business_id in session → truly unauthenticated
                # Let downstream API throw its own PermissionError (401/403) with correct message.
                return None  # type: ignore
            except Exception:
                pass
            return None  # type: ignore

        # Generic centralized session tenant resolution for ANY authenticated request
        # on erp.heshly.com / app.heshly.com that carries a valid session.
        # This is the safety net for any future frontend API on the centralized host
        # that was not explicitly listed above. It runs BEFORE Host-based resolution
        # and, when a valid session exists, correctly sets TenantContext to the
        # session's actual tenant (test_test1, etc.) instead of forcing heshly.
        # Guest / n8n requests without a session fall through to Host logic.
        try:
            _cs_user = frappe.session.user if hasattr(frappe, "session") else None  # type: ignore
            if _cs_user and _cs_user != "Guest":
                _cs_bid = frappe.session.data.get("heshly_business_id") if hasattr(frappe.session, "data") else None  # type: ignore
                if _cs_bid:
                    _cs_tenant = frappe.db.get_value("Business Account", {"business_id": _cs_bid}, "tenant_id")
                    if _cs_tenant:
                        # Only auto-apply on centralized hosts; tenant subdomain requests
                        # must keep Host-based isolation (erp.heshly.com vs {tenant}.heshly.com)
                        try:
                            _cs_host = (frappe.request.host or "").split(":")[0].lower().strip()  # type: ignore
                        except Exception:
                            _cs_host = ""
                        if _cs_host in ("erp.heshly.com", "app.heshly.com"):
                            self.context.set(_cs_tenant)
                            # For analytics/resource/API calls this is the correct tenant;
                            # return early only for non-subdomain paths (preserve subdomain flow)
                            # Check if this is an API call that should use session tenant:
                            if request_path.startswith("/api/"):
                                return _cs_tenant  # type: ignore
                        else:
                            # On tenant subdomain, let the normal Host → domain_tenant +
                            # membership check run (strict isolation). But still pre-seed
                            # TenantContext so downstream analytics using _tenant() works
                            # even if the subdomain business check later fails (defense).
                            pass
        except Exception:
            pass

        # clients.heshly.com is disabled for browser access.
        # Block at the API layer too: any authenticated API call with
        # Host=clients.heshly.com (dashboard data) must be denied even
        # if the session cookie is valid. Non-browser n8n callers already
        # use tenant_id bypass above, so only browser Host checks are hit.
        # Admins manage clients from app.heshly.com (HESHLY tenant), not here.
        try:
            _host = (getattr(frappe.request, "host", "") or "").split(":")[0].strip().lower()
            if not _host:
                _host = (frappe.get_request_header("Host") or "").split(":")[0].strip().lower()
            if not _host and hasattr(frappe.request, "headers"):
                try:
                    _host = (frappe.request.headers.get("Host") or frappe.request.headers.get("host") or "").split(",")[0].strip().lower().split(":")[0]  # type: ignore
                except Exception:
                    pass
            if _host == "clients.heshly.com":
                frappe.throw("clients.heshly.com is disabled. Use {business_id}.heshly.com (clients) or app.heshly.com (admin).", frappe.PermissionError)  # type: ignore
        except frappe.PermissionError:  # type: ignore
            raise
        except Exception:
            pass

        # Public Meta WhatsApp webhook.
        # This endpoint authenticates requests at the webhook layer,
        # not through Heshly tenant/session authentication.
        if request_path == "/api/method/heshly_core.api.whatsapp.webhook":
            self.context.clear()
            return None

        # Public n8n / Booking / Availability endpoints — tenant_id as explicit routing key.
        # For Guest (n8n) allow via tenant_id. For authenticated users keep the guard in
        # the API itself (booking membership check) but still use tenant_id to set context
        # so cross-tenant Host mismatches don't 403 before the API can return a clear error.
        if request_path in (
            "/api/method/heshly_core.api.availability.check_availability",
            "/api/method/heshly_core.api.availability.check_availability_multi",
            "/api/method/heshly_core.api.availability.check",
            "/api/method/heshly_core.api.availability.check_tolerant",
            "/api/method/heshly_core.api.booking.book_appointment",
            "/api/method/heshly_core.api.booking.create_appointment",
            "/api/method/heshly_core.api.booking.create",
            "/api/method/heshly_core.api.booking.list_appointments",
            "/api/method/heshly_core.api.booking.get",
            "/api/method/heshly_core.api.booking.cancel_appointment",
            "/api/method/heshly_core.api.booking.health",
            "/api/method/heshly_core.api.conversations.get",
            "/api/method/heshly_core.api.conversations.create",
            "/api/method/heshly_core.api.conversations.append_turn",
            "/api/method/heshly_core.api.ai.get_business_knowledge",
        ):
            try:
                data = frappe.request.get_json(silent=True) or {}
                if not isinstance(data, dict):
                    data = {}
                # also check form_dict and raw body fallback
                fd = getattr(frappe.local, "form_dict", {}) or {}
                raw = None
                try:
                    raw = getattr(frappe.request, "data", None)
                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode("utf-8", errors="ignore")
                    import json as _j
                    if isinstance(raw, str) and raw.strip().startswith("{"):
                        _pr = _j.loads(raw)
                        if isinstance(_pr, dict):
                            for _k in ("tenant_id", "tenantId", "tenant"):
                                if _k in _pr and isinstance(_pr[_k], str) and _pr[_k].strip():
                                    data.setdefault(_k, _pr[_k])
                except Exception:
                    pass
                tid = (data.get("tenant_id") or data.get("tenantId") or data.get("tenant") or fd.get("tenant_id") or fd.get("tenantId"))
                if isinstance(tid, str) and tid.strip():
                    self.context.set(tid.strip())
                    return tid.strip()
            except Exception:
                pass
            # Booking/availability are tenant_id-routed APIs — don't fall through to domain
            # Host resolution (which would default to HESHLY). Let API return clear
            # tenant_id required / membership errors.
            if request_path.startswith("/api/method/heshly_core.api.booking.") or request_path.startswith("/api/method/heshly_core.api.availability."):
                return None
            # fall through to domain resolution if no tenant_id

        # -------------------------------------------------
        # 1. Resolve Business Account from request host
        # -------------------------------------------------

        domain = (
            frappe.request.host
            .split(":")[0]
            .lower()
            .strip()
        )

        frappe.logger().debug(
            f"HOST={frappe.request.host} DOMAIN={domain} PATH={frappe.request.path}"
        )

        business = (
            self.business_repo.get_by_domain(domain)
        )

        if not business:
            raise ValueError(
                "Unable to resolve tenant from request domain."
            )

        domain_tenant = business.tenant_id

        if not domain_tenant:
            raise ValueError(
                "Business Account has no tenant_id."
            )

        # -------------------------------------------------
        # 2. Establish canonical tenant context
        # -------------------------------------------------

        self.context.set(
            domain_tenant
        )

        
        # -------------------------------------------------
        # 3. Guest requests
        #
        # Authentication MUST happen before subscription
        # entitlement is enforced.
        #
        # This allows an owner to log in even when the
        # business currently has no active subscription.
        # -------------------------------------------------

        user = frappe.session.user

        if not user or user == "Guest":

            return domain_tenant

        # -------------------------------------------------
        # 4. Resolve authenticated user's tenant
        # -------------------------------------------------

        user_tenant = (
            self.user_resolver.resolve(business.business_id)
        )

        # -------------------------------------------------
        # 6. Enforce tenant boundary
        # -------------------------------------------------

        if user_tenant != domain_tenant:

            self.context.clear()

            raise PermissionError(
                "Authenticated user does not belong "
                "to the requested tenant."
            )

        # -------------------------------------------------
        # 6. Subscription entitlement
        #
        # Subscription is intentionally checked ONLY after
        # authentication and tenant membership have been
        # established.
        # -------------------------------------------------

        frappe.logger().info(
            f"Business ID = '{business.business_id}'"
        )

        if business.business_id != "HESHLY":
            self.subscription_gate.require_access(
                business.business_id
            )

        # -------------------------------------------------
        # 7. Complete request initialization
        # -------------------------------------------------

        return domain_tenant

    # =====================================================
    # After Request
    # =====================================================

    def after_request(self) -> None:

        self.context.clear()

        self.user_resolver.clear()
