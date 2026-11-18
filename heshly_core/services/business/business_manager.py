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

from heshly_core.repositories.frappe_business_repository import (
    FrappeBusinessRepository,
)



class BusinessManager:
    """
    Business Account Manager.

    Coordinates business operations
    inside a tenant.

    Responsibilities:

    - Create businesses
    - Retrieve businesses
    - Manage profiles
    - Manage settings
    - Lifecycle control
    - Tenant validation
    """


    def __init__(self):

        self.repository = FrappeBusinessRepository()



    # =====================================================
    # Create Business
    # =====================================================

    def create(
        self,
        business: BusinessAccount,
    ) -> BusinessAccount:


        self.repository.save(
            business
        )


        return business



    # =====================================================
    # Get Business
    # =====================================================

    def get(
        self,
        business_id: str,
    ) -> BusinessAccount | None:


        return self.repository.get(
            business_id
        )



    # =====================================================
    # List Businesses
    # =====================================================

    def all(self):

        return self.repository.all()



    # =====================================================
    # Profile Management
    # =====================================================

    def update_profile(
        self,
        business_id: str,
        profile: BusinessProfile,
    ):


        business = self.get(
            business_id
        )


        if business is None:

            raise ValueError(
                "Business not found"
            )


        business.profile = profile


        self.repository.save(
            business
        )


        return business



    # =====================================================
    # Settings Management
    # =====================================================

    def update_settings(
        self,
        business_id: str,
        settings: BusinessSettings,
    ):


        business = self.get(
            business_id
        )


        if business is None:

            raise ValueError(
                "Business not found"
            )


        business.settings = settings


        self.repository.save(
            business
        )


        return business



    # =====================================================
    # Lifecycle
    # =====================================================

    def activate(
        self,
        business_id: str,
    ):


        business = self.get(
            business_id
        )


        if business is None:

            raise ValueError(
                "Business not found"
            )


        business.activate()


        self.repository.save(
            business
        )


        return business



    def suspend(
        self,
        business_id: str,
    ):


        business = self.get(
            business_id
        )


        if business is None:

            raise ValueError(
                "Business not found"
            )


        business.suspend()


        self.repository.save(
            business
        )


        return business



    # =====================================================
    # Tenant Businesses
    # =====================================================

    def for_tenant(
        self,
        tenant_id: str,
    ):


        businesses = self.repository.all()


        return [

            business

            for business in businesses

            if business.tenant_id == tenant_id

        ]



    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "business_manager",

            "status": "healthy",

        }