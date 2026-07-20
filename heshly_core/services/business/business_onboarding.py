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



class BusinessOnboarding:
    """
    Business onboarding workflow.

    Creates and configures a new business.

    Steps:

    1. Create business account
    2. Create profile
    3. Create settings
    4. Activate business

    Future:

    - Subscription setup
    - WhatsApp connection
    - AI configuration
    - Default services
    - Default workflows
    """


    def __init__(self):

        self.manager = BusinessManager()



    # =====================================================
    # Start Onboarding
    # =====================================================

    def onboard(
        self,
        business_id: str,
        tenant_id: str,
        name: str,
        industry: str | None = None,
        location: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> BusinessAccount:


        # ---------------------------------------------
        # Create Account
        # ---------------------------------------------

        business = BusinessAccount(

            business_id=business_id,

            tenant_id=tenant_id,

            name=name,

            email=email,

            phone=phone,

        )


        self.manager.create(
            business
        )


        # ---------------------------------------------
        # Create Profile
        # ---------------------------------------------

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


        # ---------------------------------------------
        # Create Settings
        # ---------------------------------------------

        settings = BusinessSettings(

            business_id=business_id,

        )


        self.manager.update_settings(

            business_id,

            settings,

        )


        # ---------------------------------------------
        # Activate
        # ---------------------------------------------

        self.manager.activate(

            business_id

        )


        return self.manager.get(
            business_id
        )



    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "business_onboarding",

            "status":
                "healthy",

        }