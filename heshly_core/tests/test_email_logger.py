from heshly_core.services.crm.email_logger import (
    EmailLogger,
    EmailDirection,
    EmailStatus,
)


def run():

    logger = EmailLogger()


    email = logger.log_email(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=EmailDirection.OUTBOUND,

        sender="sales@heshly.com",

        recipient="john@example.com",

        subject="Treatment Quotation",

        body="Please find your quotation attached.",

        status=EmailStatus.SENT,

        logged_by="Sales Agent",

    )


    print("Created Email:")
    print(email)


    assert email.direction == EmailDirection.OUTBOUND

    assert email.status == EmailStatus.SENT

    assert email.subject == "Treatment Quotation"


    history = logger.get_emails(

        "opportunity",

        "OPP-001",

    )


    print("\nEmail History:")
    print(history)


    assert len(history) == 1


    print(
        "\n✅ Email Logging Functional Test Passed"
    )


if __name__ == "__main__":

    run()