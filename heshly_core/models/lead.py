from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass(slots=True)
class Lead:

    lead_id: str

    tenant_id: str

    name: str

    email: str | None = None

    phone: str | None = None

    status: str = "new"

    source: str | None = None

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(UTC)
    )


    def qualify(self):

        self.status = "qualified"



    def close(self):

        self.status = "closed"
