from heshly_core.models.crm import Lead

from heshly_core.repositories.lead_repository import (
    LeadRepository,
)


def run():

    repo = LeadRepository()

    lead = Lead(

        lead_id="LEAD-001",

        business_id="BIZ-001",

        full_name="John Doe",

        phone="+254700123456",

        email="john@example.com",

        company="ABC Ltd",

    )

    repo.save(lead)

    assert repo.count() == 1

    assert repo.exists("LEAD-001")

    assert repo.get("LEAD-001") == lead

    assert repo.find_by_email(
        "john@example.com"
    ) == lead

    assert repo.find_by_phone(
        "+254700123456"
    ) == lead

    assert len(repo.search("john")) == 1

    assert repo.delete("LEAD-001")

    assert repo.count() == 0

    print(
        "✅ Lead Repository Functional Test Passed"
    )


if __name__ == "__main__":

    run()