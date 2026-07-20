from heshly_core.services.ai.industry_ai_templates import (
    IndustryAITemplates,
)


def run_test():

    print("\n==============================")
    print("Industry AI Templates Test")
    print("==============================\n")

    templates = IndustryAITemplates()

    dental = templates.load("dental")

    assert dental.name == "Dental Receptionist"

    print("✅ Dental template")

    salon = templates.load("salon")

    assert salon.name == "Salon Receptionist"

    print("✅ Salon template")

    logistics = templates.load("logistics")

    assert logistics.name == "Logistics Assistant"

    print("✅ Logistics template")

    insurance = templates.load("insurance")

    assert insurance.name == "Insurance Advisor"

    print("✅ Insurance template")

    real_estate = templates.load("real_estate")

    assert real_estate.name == "Property Assistant"

    print("✅ Real Estate template")

    print("\n🎉 INDUSTRY AI TEMPLATE TEST PASSED\n")


if __name__ == "__main__":

    run_test()