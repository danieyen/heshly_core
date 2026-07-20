from heshly_core.models.team_member import (
    TeamMember,
    TeamMemberStatus,
    TeamMemberType,
)



def run_test():

    print("\n==============================")
    print("Team Member Model Test")
    print("==============================\n")



    member = TeamMember(

        member_id="member_001",

        business_id="business_001",

        user_id="user_001",

        name="Mary Wanjiku",

        job_title="Receptionist",

        department="Front Desk",

        member_type=TeamMemberType.EMPLOYEE,

    )



    assert member.member_id == "member_001"


    print("✅ Member creation passed")



    assert (
        member.business_id
        ==
        "business_001"
    )


    print("✅ Business ownership passed")



    assert (
        member.job_title
        ==
        "Receptionist"
    )


    print("✅ Job title passed")



    assert (
        member.status
        ==
        TeamMemberStatus.ACTIVE
    )


    print("✅ Default status passed")



    member.mark_leave()


    assert (
        member.status
        ==
        TeamMemberStatus.ON_LEAVE
    )


    print("✅ Leave status passed")



    member.suspend()


    assert (
        member.status
        ==
        TeamMemberStatus.SUSPENDED
    )


    print("✅ Suspension passed")



    member.activate()


    assert member.is_active


    print("✅ Activation passed")



    print("\n🎉 TEAM MEMBER MODEL TEST PASSED\n")



if __name__ == "__main__":

    run_test()