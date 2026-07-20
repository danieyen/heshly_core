from heshly_core.services.crm.activity_manager import (
    ActivityManager,
)

from heshly_core.services.crm.task_manager import (
    TaskPriority,
    TaskStatus,
)

from heshly_core.services.crm.call_logger import (
    CallDirection,
    CallOutcome,
)

from heshly_core.services.crm.email_logger import (
    EmailDirection,
    EmailStatus,
)

from heshly_core.services.crm.whatsapp_activity_logger import (
    WhatsAppDirection,
    WhatsAppMessageStatus,
)


def run():

    print("========================================")
    print(" Heshly CRM Activity Management Test")
    print("========================================\n")

    manager = ActivityManager()

    # =====================================
    # Note
    # =====================================

    note = manager.create_note(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        title="Consultation Summary",

        content="Customer is interested in the premium package.",

        created_by="Sales Agent",

    )

    print("✓ Note Created")

    # =====================================
    # Task
    # =====================================

    task = manager.create_task(

        business_id="BIZ-001",

        title="Call customer tomorrow",

        related_type="opportunity",

        related_id="OPP-001",

        assigned_to="Sales Agent",

        priority=TaskPriority.HIGH,

    )

    print("✓ Task Created")

    manager.complete_task(
        task.task_id
    )

    assert task.status == TaskStatus.COMPLETED

    print("✓ Task Completed")

    # =====================================
    # Call
    # =====================================

    call = manager.log_call(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=CallDirection.OUTBOUND,

        phone_number="+254700123456",

        duration_seconds=360,

        outcome=CallOutcome.ANSWERED,

        notes="Discussed pricing.",

        logged_by="Sales Agent",

    )

    print("✓ Call Logged")

    # =====================================
    # Email
    # =====================================

    email = manager.log_email(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=EmailDirection.OUTBOUND,

        sender="sales@heshly.com",

        recipient="john@example.com",

        subject="Quotation",

        body="Please find your quotation attached.",

        status=EmailStatus.SENT,

        logged_by="Sales Agent",

    )

    print("✓ Email Logged")

    # =====================================
    # WhatsApp
    # =====================================

    whatsapp = manager.log_whatsapp(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=WhatsAppDirection.OUTBOUND,

        phone_number="+254700123456",

        message="I've emailed your quotation.",

        status=WhatsAppMessageStatus.SENT,

        logged_by="AI Receptionist",

    )

    print("✓ WhatsApp Logged")

    # =====================================
    # Timeline
    # =====================================

    timeline = manager.build_timeline(

        notes=[note],

        tasks=[task],

        calls=[call],

        emails=[email],

        whatsapp=[whatsapp],

    )

    print("\nCustomer Timeline\n")

    for event in timeline:

        print(
            f"{event.event_type:<12} | {event.title}"
        )

    assert len(timeline) == 5

    print("\n✓ Timeline Built")

    print("\n========================================")
    print("✅ Activity Manager Functional Test Passed")
    print("========================================")


if __name__ == "__main__":
    run()