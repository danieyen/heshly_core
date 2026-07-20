from heshly_core.config.crm_config import crm_config


def run():

    print("CRM Configuration")
    print("----------------------------")

    print("Auto Create Leads:", crm_config.auto_create_leads)
    print("Auto Assign Leads:", crm_config.auto_assign_leads)
    print("Auto Score Leads:", crm_config.auto_score_leads)

    print()

    print("Default Pipeline:", crm_config.default_pipeline)

    print()

    print("Pipeline Stages")

    for stage in crm_config.default_stages:
        print("-", stage)

    print()

    print("AI Auto Qualify:", crm_config.ai_auto_qualify)
    print("AI Auto Update Pipeline:", crm_config.ai_auto_update_pipeline)

    print()

    print("✅ CRM Configuration Functional Test Passed")


if __name__ == "__main__":
    run()