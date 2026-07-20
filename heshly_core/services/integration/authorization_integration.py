from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AuthorizationResult:
    """
    Result returned after authorization checks.
    """

    allowed: bool

    permission: str | None = None

    message: str | None = None



class AuthorizationIntegration:
    """
    High-level authorization orchestration layer.

    Connects RBAC, permissions, API security,
    and audit logging.
    """

    def __init__(
        self,
        authorization_manager,
        permission_manager,
        api_key_manager,
        request_signature_validator,
        webhook_verifier,
        audit_service,
        security_metrics,
    ):

        self.authorization_manager = authorization_manager

        self.permission_manager = permission_manager

        self.api_key_manager = api_key_manager

        self.request_signature_validator = (
            request_signature_validator
        )

        self.webhook_verifier = webhook_verifier

        self.audit_service = audit_service

        self.security_metrics = security_metrics


    # =====================================================
    # Permission Authorization
    # =====================================================

    def authorize(
        self,
        user,
        resource: str,
        action: str,
    ) -> AuthorizationResult:

        allowed = self.authorization_manager.has_permission(
            user,
            resource,
            action,
        )


        if allowed:

            self.security_metrics.increment(
                "authorization_success"
            )

            return AuthorizationResult(

                allowed=True,

                permission=f"{resource}.{action}",

                message="Permission granted",

            )


        self.security_metrics.increment(
            "authorization_denied"
        )


        self.audit_service.access_denied(

            tenant_id=getattr(
                user,
                "tenant_id",
                None,
            ),

            user_id=user.user_id,

            resource=resource,

        )


        return AuthorizationResult(

            allowed=False,

            permission=f"{resource}.{action}",

            message="Permission denied",

        )


    # =====================================================
    # API Key Validation
    # =====================================================

    def validate_api_key(
        self,
        api_key: str,
    ):

        return self.api_key_manager.validate(
            api_key
        )


    # =====================================================
    # Request Signature
    # =====================================================

    def validate_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
    ):

        return self.request_signature_validator.validate(
            payload,
            signature,
            secret,
        )


    # =====================================================
    # Webhook Verification
    # =====================================================

    def verify_webhook(
        self,
        payload,
        signature,
    ):

        return self.webhook_verifier.verify(
            payload,
            signature,
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "authorization_integration",

            "status": "healthy",

        }