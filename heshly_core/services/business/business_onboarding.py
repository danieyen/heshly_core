from __future__ import annotations

from heshly_core.models.business_account import (
    BusinessAccount,
)

from heshly_core.models.business_profile import (
    BusinessProfile,
)

from heshly_core.models.business_settings import (
    BusinessSettings,
)

from heshly_core.services.business.business_manager import (
    BusinessManager,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class BusinessOnboarding:
    """
    Business onboarding workflow.

    Tenant ownership is always derived from TenantContext.

    A domain is required because the Frappe Business Account
    DocType requires it.
    """

    def __init__(self):

        self.manager = BusinessManager()
        self.context = TenantContext()

    # =====================================================
    # Start Onboarding
    # =====================================================

    def onboard(
        self,
        business_id: str,
        name: str,
        domain: str,
        industry: str | None = None,
        location: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> BusinessAccount:

        tenant_id = self.context.require()

        if not domain:
            raise ValueError(
                "domain is required."
            )

        domain = domain.lower().strip()

        business = BusinessAccount(
            business_id=business_id,
            tenant_id=tenant_id,
            name=name,
            domain=domain,
            email=email,
            phone=phone,
        )

        self.manager.create(
            business
        )

        profile = BusinessProfile(
            business_id=business_id,
            name=name,
            industry=industry,
            location=location,
            email=email,
            phone=phone,
        )

        self.manager.update_profile(
            business_id,
            profile,
        )

        settings = BusinessSettings(
            business_id=business_id,
        )

        self.manager.update_settings(
            business_id,
            settings,
        )

        self.manager.activate(
            business_id
        )

        result = self.manager.get(
            business_id
        )

        if result is None:
            raise RuntimeError(
                "Business onboarding completed but "
                "the business could not be reloaded."
            )

        return result

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {
            "service": "business_onboarding",
            "status": "healthy",
            "tenant": self.context.get() is not None,
        }
