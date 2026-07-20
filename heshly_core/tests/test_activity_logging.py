from heshly_core.services.crm.activity_logger import (
    ActivityLogger,
)

from heshly_core.models.activity import (
    ActivityPriority,
)



def run():

    logger = ActivityLogger()



    # Log WhatsApp activity

    activity = logger.log(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        activity_type="whatsapp",

        subject="Sent quotation",

        description="Customer received treatment quotation",

        assigned_to="Sales Agent",

    )


    print(
        "Created Activity:"
    )

    print(activity)



    assert activity.activity_type == (
        "whatsapp"
    )



    assert activity.status.value == (
        "pending"
    )



    # Log second activity

    logger.log(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        activity_type="call",

        subject="Pricing discussion",

        priority=ActivityPriority.HIGH,

    )



    history = logger.get_history(

        "opportunity",

        "OPP-001",

    )


    print(
        "\nActivity History:"
    )


    for item in history:

        print(item)



    assert len(history) == 2



    print(
        "\n✅ Activity Logging Functional Test Passed"
    )



if __name__ == "__main__":

    run()