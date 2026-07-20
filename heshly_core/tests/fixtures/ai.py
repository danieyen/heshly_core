def conversation_fixture():

    return {

        "conversation_id": "conversation001",

        "tenant_id": "tenant001",

        "user_id": "user001",

        "channel": "whatsapp",

        "status": "active",

    }



def ai_session_fixture():

    return {

        "session_id": "ai_session001",

        "tenant_id": "tenant001",

        "conversation_id": "conversation001",

        "status": "active",

    }



def intent_fixture():

    return {

        "intent": "BOOK_APPOINTMENT",

        "confidence": 0.95,

    }
