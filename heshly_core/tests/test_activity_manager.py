from heshly_core.services.crm.activity_manager import (
    ActivityManager,
)

from heshly_core.services.crm.call_logger import (
    CallDirection,
)

from heshly_core.services.crm.email_logger import (
    EmailDirection,
)

from heshly_core.services.crm.whatsapp_activity_logger import (
    WhatsAppDirection,
    WhatsAppMessageStatus,
)


def run():

    manager = ActivityManager()

    # -------------------------------
    # Note
    # -------------------------------

    note = manager.create_note(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        title="Consultation",

        content="Customer requested financing.",

    )

    # -------------------------------
    # Call
    # -------------------------------

    call = manager.log_call(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=CallDirection.OUTBOUND,

        phone_number="+254700000000",

    )

    # -------------------------------
    # Email
    # -------------------------------

    email = manager.log_email(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=EmailDirection.OUTBOUND,

        sender="sales@heshly.com",

        recipient="john@example.com",

        subject="Quotation",

        body="Attached quotation.",

    )

    # -------------------------------
    # WhatsApp
    # -------------------------------

    whatsapp = manager.log_whatsapp(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=WhatsAppDirection.OUTBOUND,

        phone_number="+254700000000",

        message="Your quotation has been sent.",

        status=WhatsAppMessageStatus.SENT,

    )

    # -------------------------------
    # Timeline
    # -------------------------------

    timeline = manager.build_timeline(

        notes=[note],

        calls=[call],

        emails=[email],

        whatsapp=[whatsapp],

    )

    print("\nTimeline\n")

    for event in timeline:

        print(event.event_type, "-", event.title)

    assert len(timeline) == 4

    print("\n✅ Activity Manager Functional Test Passed")


if __name__ == "__main__":
    run()