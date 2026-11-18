from dataclasses import dataclass


from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.tenant.repository_tenant_filter import (
    RepositoryTenantFilter,
)



@dataclass
class AIProfile:

    tenant_id: str

    industry: str

    personality: str

    system_prompt: str



def run_test():

    print("\n================================")
    print("AI Customization Test")
    print("================================\n")


    context = TenantContext()

    filter_service = RepositoryTenantFilter()


    # ==========================================
    # Create Tenants
    # ==========================================

    dental_tenant = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

    )


    salon_tenant = Tenant(

        tenant_id="tenant002",

        name="Elite Salon",

    )


    print(
        "✅ Tenants created"
    )


    # ==========================================
    # AI Profiles
    # ==========================================

    profiles = [

        AIProfile(

            tenant_id="tenant001",

            industry="Dental",

            personality="Professional",

            system_prompt=
            "You are a dental clinic assistant",

        ),


        AIProfile(

            tenant_id="tenant002",

            industry="Salon",

            personality="Friendly",

            system_prompt=
            "You are a salon booking assistant",

        ),

    ]


    print(
        "✅ AI profiles created"
    )


    # ==========================================
    # Dental Tenant Context
    # ==========================================

    context.set(
        dental_tenant
    )


    dental_profile = filter_service.filter(
        profiles
    )


    assert len(
        dental_profile
    ) == 1


    assert (
        dental_profile[0].industry
        ==
        "Dental"
    )


    assert (
        dental_profile[0].personality
        ==
        "Professional"
    )


    print(
        "✅ Dental AI customization isolated"
    )


    # ==========================================
    # Salon Tenant Context
    # ==========================================

    context.set(
        salon_tenant
    )


    salon_profile = filter_service.filter(
        profiles
    )


    assert len(
        salon_profile
    ) == 1


    assert (
        salon_profile[0].industry
        ==
        "Salon"
    )


    assert (
        salon_profile[0].personality
        ==
        "Friendly"
    )


    print(
        "✅ Salon AI customization isolated"
    )


    # ==========================================
    # Cross Tenant Protection
    # ==========================================

    assert (

        dental_profile[0].tenant_id

        !=

        salon_profile[0].tenant_id

    )


    print(
        "✅ AI cross tenant access prevented"
    )


    context.clear()


    print(
        "✅ Context cleared"
    )


    print(
        "\n🎉 AI CUSTOMIZATION TEST PASSED\n"
    )



if __name__ == "__main__":

    run_test()