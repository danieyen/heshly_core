from heshly_core.services.configuration.industry_templates import (
    IndustryTemplates,
)


def run_test():

    print("\n==============================")
    print("Industry Templates Test")
    print("==============================\n")

    templates = IndustryTemplates()

    dental = templates.load("dental")

    assert dental.get("industry") == "Dental Clinic"

    print("✅ Dental template")

    salon = templates.load("salon")

    assert salon.get("industry") == "Salon"

    print("✅ Salon template")

    real_estate = templates.load("real_estate")

    assert real_estate.get("industry") == "Real Estate"

    print("✅ Real Estate template")

    logistics = templates.load("logistics")

    assert logistics.get("industry") == "Logistics"

    print("✅ Logistics template")

    insurance = templates.load("insurance")

    assert insurance.get("industry") == "Insurance"

    print("✅ Insurance template")

    print("\n🎉 INDUSTRY TEMPLATE TEST PASSED\n")


if __name__ == "__main__":

    run_test()