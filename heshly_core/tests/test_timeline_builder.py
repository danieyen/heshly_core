from heshly_core.services.crm.timeline_builder import (
    TimelineBuilder,
)

from heshly_core.services.crm.note_manager import (
    NoteManager,
)

from heshly_core.services.crm.call_logger import (
    CallLogger,
    CallDirection,
)

from heshly_core.services.crm.email_logger import (
    EmailLogger,
    EmailDirection,
)

from heshly_core.services.crm.whatsapp_activity_logger import (
    WhatsAppActivityLogger,
    WhatsAppDirection,
    WhatsAppMessageStatus,
)



def run():

    builder = TimelineBuilder()


    note_manager = NoteManager()
    call_logger = CallLogger()
    email_logger = EmailLogger()
    whatsapp_logger = WhatsAppActivityLogger()


    note = note_manager.create_note(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        title="Consultation",

        content="Customer wants financing.",

    )


    call = call_logger.log_call(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=CallDirection.OUTBOUND,

        phone_number="+254700000000",

    )


    email = email_logger.log_email(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=EmailDirection.OUTBOUND,

        sender="sales@heshly.com",

        recipient="john@example.com",

        subject="Quotation",

        body="Quotation attached.",

    )


    whatsapp = whatsapp_logger.log_message(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=WhatsAppDirection.OUTBOUND,

        phone_number="+254700000000",

        message="Your quotation has been sent.",

        status=WhatsAppMessageStatus.SENT,

    )


    timeline = builder.build(

        notes=[note],

        calls=[call],

        emails=[email],

        whatsapp=[whatsapp],

    )


    print("\nCustomer Timeline\n")

    for event in timeline:

        print(

            event.created_at,

            event.event_type,

            event.title,

        )


    assert len(timeline) == 4

    print(
        "\n✅ Timeline Builder Functional Test Passed"
    )


if __name__ == "__main__":

    run()