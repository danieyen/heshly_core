from heshly_core.services.crm.missed_appointment_recovery import (
    MissedAppointmentRecovery,
)

from heshly_core.services.crm.reminder_scheduler import (
    ReminderScheduler,
)


def run():

    scheduler = ReminderScheduler()

    recovery = MissedAppointmentRecovery(
        scheduler
    )

    follow_up = recovery.recover(

        business_id="BIZ-001",

        appointment_id="APT-001",

        customer_name="John Doe",

        assigned_to="Receptionist",

    )

    print("Recovery Follow-up:")
    print(follow_up)

    assert follow_up.related_type == "appointment"

    assert follow_up.related_id == "APT-001"

    assert "Recover missed appointment" in (
        follow_up.subject
    )

    assert len(scheduler.follow_ups) == 1

    print(
        "\n✅ Missed Appointment Recovery Functional Test Passed"
    )


if __name__ == "__main__":

    run()