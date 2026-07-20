from heshly_core.tests.utils import (
    generate_user_id,
    generate_tenant_id,
    build_event,
    Timer,
)



def test_factories():

    assert generate_user_id()

    assert generate_tenant_id()



def test_event_builder():

    event = build_event(
        "login"
    )

    assert event["event_type"] == "login"



def test_timer():

    timer = Timer()

    timer.start()

    timer.stop()

    assert timer.elapsed >= 0
