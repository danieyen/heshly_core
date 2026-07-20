from __future__ import annotations

import uuid

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class CRMNote:

    note_id: str

    business_id: str

    related_type: str

    related_id: str

    title: str

    content: str

    created_by: str | None = None

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )



class NoteManagementError(Exception):
    pass



class NoteManager:

    def __init__(self):

        self.notes: list[CRMNote] = []



    def create_note(
        self,
        business_id: str,
        related_type: str,
        related_id: str,
        title: str,
        content: str,
        created_by: str | None = None,
    ) -> CRMNote:


        if not business_id:

            raise NoteManagementError(
                "Business ID is required."
            )


        if not related_id:

            raise NoteManagementError(
                "Related ID is required."
            )


        if not title.strip():

            raise NoteManagementError(
                "Note title is required."
            )


        if not content.strip():

            raise NoteManagementError(
                "Note content is required."
            )


        note = CRMNote(

            note_id=self._generate_id(),

            business_id=business_id,

            related_type=related_type,

            related_id=related_id,

            title=title,

            content=content,

            created_by=created_by,

        )


        self.notes.append(note)

        return note



    def get_notes(
        self,
        related_type: str,
        related_id: str,
    ) -> list[CRMNote]:


        return [

            note

            for note in self.notes

            if (
                note.related_type == related_type
                and
                note.related_id == related_id
            )

        ]



    def delete_note(
        self,
        note_id: str,
    ) -> bool:


        for index, note in enumerate(self.notes):

            if note.note_id == note_id:

                del self.notes[index]

                return True


        raise NoteManagementError(
            "Note not found."
        )



    def _generate_id(self):

        return (
            f"NOTE-{uuid.uuid4().hex[:8].upper()}"
        )