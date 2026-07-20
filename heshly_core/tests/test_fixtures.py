def test_fixtures(
    tenant,
    user,
    customer,
    appointment,
    lead,
    session,
    token,
    conversation,
    intent,
):

    assert tenant["tenant_id"] == "tenant001"

    assert user["user_id"] == "user001"

    assert customer["customer_id"]

    assert appointment["appointment_id"]

    assert lead["lead_id"]

    assert session["session_id"]

    assert token["access_token"]

    assert conversation["conversation_id"]

    assert intent["intent"] == "BOOK_APPOINTMENT"
