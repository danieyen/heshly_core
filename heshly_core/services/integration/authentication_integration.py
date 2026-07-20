from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AuthenticationResult:
    """
    Result returned after authentication.
    """

    success: bool

    user: Any | None = None

    session: Any | None = None

    access_token: str | None = None

    refresh_token: str | None = None

    jwt: str | None = None

    message: str | None = None


class AuthenticationIntegration:
    """
    High-level authentication orchestration layer.

    Connects authentication, sessions, tokens,
    auditing, and security monitoring.
    """

    def __init__(
        self,
        authentication_service,
        login_manager,
        session_manager,
        token_manager,
        jwt_manager,
        refresh_token_manager,
        token_revocation,
        brute_force_protection,
        account_lockout,
        audit_service,
        security_metrics,
    ):

        self.authentication_service = authentication_service

        self.login_manager = login_manager

        self.session_manager = session_manager

        self.token_manager = token_manager

        self.jwt_manager = jwt_manager

        self.refresh_token_manager = refresh_token_manager

        self.token_revocation = token_revocation

        self.brute_force_protection = brute_force_protection

        self.account_lockout = account_lockout

        self.audit_service = audit_service

        self.security_metrics = security_metrics


    # =====================================================
    # Login
    # =====================================================

    def login(
        self,
        username: str,
        password: str,
        tenant_id: str | None = None,
    ) -> AuthenticationResult:

        if self.account_lockout.is_locked(
            username
        ):

            return AuthenticationResult(
                success=False,
                message="Account locked",
            )


        if self.brute_force_protection.is_blocked(
            username
        ):

            return AuthenticationResult(
                success=False,
                message="Login temporarily blocked",
            )


        user = self.authentication_service.authenticate(
            username,
            password,
        )


        if user is None:

            self.brute_force_protection.record_failure(
                username
            )

            self.security_metrics.increment(
                "failed_logins"
            )

            return AuthenticationResult(
                success=False,
                message="Invalid credentials",
            )


        self.brute_force_protection.reset(
            username
        )


        session = self.session_manager.create(
            user.user_id,
            tenant_id,
        )


        access_token = self.token_manager.create(
            user.user_id
        )


        refresh_token = self.refresh_token_manager.create(
            user.user_id
        )


        jwt = self.jwt_manager.create(
            user.user_id
        )


        self.audit_service.login(
            tenant_id=tenant_id,
            user_id=user.user_id,
        )


        self.security_metrics.increment(
            "successful_logins"
        )


        return AuthenticationResult(

            success=True,

            user=user,

            session=session,

            access_token=access_token,

            refresh_token=refresh_token,

            jwt=jwt,

            message="Authentication successful",

        )


    # =====================================================
    # Logout
    # =====================================================

    def logout(
        self,
        user_id: str,
        session_id: str,
        token: str | None = None,
        tenant_id: str | None = None,
    ):

        if token:

            self.token_revocation.revoke(
                token
            )


        self.session_manager.revoke(
            session_id
        )


        self.audit_service.logout(
            tenant_id=tenant_id,
            user_id=user_id,
        )


        return {
            "success": True,
            "message": "Logged out",
        }


    # =====================================================
    # Token Validation
    # =====================================================

    def validate_request(
        self,
        token: str,
    ):

        if self.token_revocation.is_revoked(
            token
        ):

            return None


        return self.jwt_manager.verify(
            token
        )


    # =====================================================
    # Refresh
    # =====================================================

    def refresh(
        self,
        refresh_token: str,
    ):

        user_id = self.refresh_token_manager.validate(
            refresh_token
        )

        if user_id is None:

            return None


        new_access = self.token_manager.create(
            user_id
        )


        new_refresh = self.refresh_token_manager.rotate(
            refresh_token
        )


        new_jwt = self.jwt_manager.create(
            user_id
        )


        return {

            "access_token": new_access,

            "refresh_token": new_refresh,

            "jwt": new_jwt,

        }


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "authentication_integration",

            "status": "healthy",

        }