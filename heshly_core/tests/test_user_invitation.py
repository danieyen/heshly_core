from heshly_core.models.user_invitation import (
    InvitationStatus,
    UserInvitation,
)

from heshly_core.services.team.user_invitation_manager import (
    UserInvitationManager,
)


def run_test():

    print("\n==============================")
    print("User Invitation Test")
    print("==============================\n")

    manager = UserInvitationManager()

    manager.clear()

    invitation = UserInvitation(

        invitation_id="invite_001",

        tenant_id="tenant_001",

        business_id="business_001",

        email="mary@example.com",

        role="receptionist",

        invited_by="owner_001",

    )

    manager.create(
        invitation
    )

    print("✅ Invitation creation passed")

    assert manager.get(
        "invite_001"
    ) is not None

    print("✅ Retrieval passed")

    manager.accept(
        "invite_001"
    )

    assert (
        manager.get("invite_001").status
        ==
        InvitationStatus.ACCEPTED
    )

    print("✅ Acceptance passed")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check passed")

    print("\n🎉 USER INVITATION TEST PASSED\n")


if __name__ == "__main__":

    run_test()