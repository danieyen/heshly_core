from heshly_core.models.tenant import (
    Tenant,
    TenantConfiguration,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)

from heshly_core.services.tenant.repository_tenant_filter import (
    RepositoryTenantFilter,
)

from dataclasses import dataclass


@dataclass
class ConfigurationRecord:

    tenant_id: str

    industry: str

    currency: str

    language: str



def run_test():

    print("\n================================")
    print("Configuration Test")
    print("================================\n")


    context = TenantContextManager()

    filter_service = RepositoryTenantFilter()


    # ==========================================
    # Tenant Creation
    # ==========================================

    dental = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

        configuration=TenantConfiguration(

            industry="Dental",

            currency="KES",

            language="en",

        ),

    )


    salon = Tenant(

        tenant_id="tenant002",

        name="Elite Salon",

        configuration=TenantConfiguration(

            industry="Salon",

            currency="KES",

            language="en",

        ),

    )


    print(
        "✅ Tenant configurations created"
    )


    configurations = [

        ConfigurationRecord(

            tenant_id="tenant001",

            industry="Dental",

            currency="KES",

            language="en",

        ),


        ConfigurationRecord(

            tenant_id="tenant002",

            industry="Salon",

            currency="KES",

            language="en",

        ),

    ]


    # ==========================================
    # Dental Tenant Context
    # ==========================================

    context.set(
        dental
    )


    dental_config = filter_service.filter(
        configurations
    )


    assert len(
        dental_config
    ) == 1


    assert (
        dental_config[0].industry
        ==
        "Dental"
    )


    print(
        "✅ Dental configuration isolated"
    )


    # ==========================================
    # Salon Tenant Context
    # ==========================================

    context.set(
        salon
    )


    salon_config = filter_service.filter(
        configurations
    )


    assert len(
        salon_config
    ) == 1


    assert (
        salon_config[0].industry
        ==
        "Salon"
    )


    print(
        "✅ Salon configuration isolated"
    )


    # ==========================================
    # Cross Tenant Prevention
    # ==========================================

    assert (

        dental_config[0].tenant_id

        !=

        salon_config[0].tenant_id

    )


    print(
        "✅ Cross tenant configuration blocked"
    )


    context.clear()


    print(
        "✅ Context cleared"
    )


    print(
        "\n🎉 CONFIGURATION TEST PASSED\n"
    )



if __name__ == "__main__":

    run_test()