from heshly_core.models.team_member import (
    TeamMember,
)

from heshly_core.repositories.team_repository import (
    TeamRepository,
)


def run_test():

    print("\n==============================")
    print("Team Repository Test")
    print("==============================\n")

    repository = TeamRepository()

    repository.clear()

    member = TeamMember(

        member_id="member_001",

        business_id="business_001",

        user_id="user_001",

        name="Mary Wanjiku",

        job_title="Receptionist",

    )

    repository.save(
        member
    )

    print("✅ Save passed")

    stored = repository.get(
        "member_001"
    )

    assert stored is not None

    print("✅ Retrieval passed")

    assert repository.count() == 1

    print("✅ Count passed")

    members = repository.by_business(
        "business_001"
    )

    assert len(members) == 1

    print("✅ Business lookup passed")

    repository.delete(
        "member_001"
    )

    assert repository.count() == 0

    print("✅ Delete passed")

    print("\n🎉 TEAM REPOSITORY TEST PASSED\n")


if __name__ == "__main__":

    run_test()