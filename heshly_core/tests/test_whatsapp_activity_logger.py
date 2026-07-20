from heshly_core.services.crm.whatsapp_activity_logger import (
    WhatsAppActivityLogger,
    WhatsAppDirection,
    WhatsAppMessageStatus,
)


def run():

    logger = WhatsAppActivityLogger()


    activity = logger.log_message(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=WhatsAppDirection.OUTBOUND,

        phone_number="+254700123456",

        message="Hello John, your quotation is ready.",

        status=WhatsAppMessageStatus.SENT,

        logged_by="AI Receptionist",

    )


    print("Created WhatsApp Activity:")
    print(activity)


    assert activity.direction == (
        WhatsAppDirection.OUTBOUND
    )

    assert activity.status == (
        WhatsAppMessageStatus.SENT
    )



    history = logger.get_history(

        "opportunity",

        "OPP-001",

    )


    print("\nWhatsApp History:")

    print(history)


    assert len(history) == 1


    print(
        "\n✅ WhatsApp Activity Logging Functional Test Passed"
    )


if __name__ == "__main__":

    run()