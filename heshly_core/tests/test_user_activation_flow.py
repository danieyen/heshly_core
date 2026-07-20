from heshly_core.models.team_member import (
    TeamMember,
)

from heshly_core.models.user import (
    User,
    UserStatus,
)

from heshly_core.models.user_invitation import (
    InvitationStatus,
    UserInvitation,
)

from heshly_core.services.team.user_activation_flow import (
    UserActivationFlow,
)


def run_test():

    print("\n==============================")
    print("User Activation Flow Test")
    print("==============================\n")

    invitation = UserInvitation(

        invitation_id="invite_001",

        tenant_id="tenant_001",

        business_id="business_001",

        email="mary@example.com",

        role="receptionist",

        invited_by="owner_001",

    )

    invitation.accept()

    user = User(

        user_id="user_001",

        tenant_id="tenant_001",

        name="Mary",

        email="mary@example.com",

    )

    user.deactivate()

    member = TeamMember(

        member_id="member_001",

        business_id="business_001",

        user_id="user_001",

        name="Mary",

        job_title="Receptionist",

    )

    member.deactivate()

    flow = UserActivationFlow()

    assert flow.can_activate(
        invitation
    )

    print("✅ Activation validation passed")

    flow.activate(
        invitation,
        user,
        member,
    )

    assert user.status == UserStatus.ACTIVE

    print("✅ User activation passed")

    assert member.is_active

    print("✅ Team member activation passed")

    assert flow.health()["status"] == "healthy"

    print("✅ Health check passed")

    print("\n🎉 USER ACTIVATION FLOW TEST PASSED\n")


if __name__ == "__main__":

    run_test()