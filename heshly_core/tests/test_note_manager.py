from heshly_core.services.crm.note_manager import (
    NoteManager,
    NoteManagementError,
)


def run():

    manager = NoteManager()


    note = manager.create_note(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        title="Consultation Summary",

        content="Customer agreed to proceed with treatment.",

        created_by="Sales Agent",

    )


    print("Created Note:")
    print(note)


    assert note.title == "Consultation Summary"


    notes = manager.get_notes(

        "opportunity",

        "OPP-001",

    )


    print("\nRelated Notes:")
    print(notes)


    assert len(notes) == 1


    deleted = manager.delete_note(
        note.note_id
    )


    print("\nDeleted:", deleted)


    assert deleted is True


    try:

        manager.delete_note(
            note.note_id
        )


    except NoteManagementError as error:

        print("\nExpected Error:")
        print(error)


    else:

        raise Exception(
            "Deleting a missing note should fail."
        )


    print(
        "\n✅ Notes Management Functional Test Passed"
    )


if __name__ == "__main__":

    run()