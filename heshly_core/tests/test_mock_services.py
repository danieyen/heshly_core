def test_mock_services(
    whatsapp_service,
    calendar_service,
    payment_service,
    ai_service,
    notification_service,
):

    assert (
        whatsapp_service.health()["status"]
        ==
        "healthy"
    )


    whatsapp_service.send_message(
        "+254700000000",
        "Hello",
    )

    assert len(
        whatsapp_service.get_messages()
    ) == 1


    calendar_service.create_event(
        "Meeting",
        "10:00",
        "11:00",
    )

    assert len(
        calendar_service.list_events()
    ) == 1


    payment = payment_service.charge(
        "customer001",
        1000,
    )

    assert payment["status"] == "success"


    ai = ai_service.generate_response(
        "Book appointment"
    )

    assert ai["confidence"] == 0.95


    notification = notification_service.send(
        "test@test.com",
        "Welcome",
    )

    assert notification["status"] == "sent"

