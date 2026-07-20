from __future__ import annotations


class SecurityHealthCheck:
    """
    Central security subsystem health checker.

    Validates availability of:
    - Authentication
    - Authorization
    - Encryption
    - Audit
    - Monitoring
    """

    def __init__(
        self,
        authentication_integration,
        authorization_integration,
        encryption_integration,
        audit_integration,
        security_metrics,
        security_dashboard,
    ):

        self.authentication = authentication_integration

        self.authorization = authorization_integration

        self.encryption = encryption_integration

        self.audit = audit_integration

        self.metrics = security_metrics

        self.dashboard = security_dashboard


    # =====================================================
    # Full Security Health
    # =====================================================

    def check(self):

        checks = {

            "authentication":
                self.authentication.health(),

            "authorization":
                self.authorization.health(),

            "encryption":
                self.encryption.health(),

            "audit":
                self.audit.health(),

            "metrics":
                self.metrics.health(),

            "dashboard":
                self.dashboard.health(),

        }


        healthy = all(
            item.get("status") == "healthy"
            for item in checks.values()
        )


        return {

            "status":
                "healthy"
                if healthy
                else "unhealthy",

            "components": checks,

        }


    # =====================================================
    # Individual Component
    # =====================================================

    def is_healthy(self):

        return (
            self.check()["status"]
            ==
            "healthy"
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "security_health_check",

            "status":
                "healthy",

        }