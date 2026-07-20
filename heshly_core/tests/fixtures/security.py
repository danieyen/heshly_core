from datetime import datetime, UTC, timedelta



def session_fixture():

    return {

        "session_id": "session001",

        "user_id": "user001",

        "tenant_id": "tenant001",

        "created_at": datetime.now(UTC),

        "expires_at":
            datetime.now(UTC)
            +
            timedelta(hours=8),

    }



def token_fixture():

    return {

        "access_token": "test-access-token",

        "refresh_token": "test-refresh-token",

        "user_id": "user001",

        "tenant_id": "tenant001",

    }



def security_context_fixture():

    return {

        "tenant_id": "tenant001",

        "user_id": "user001",

        "ip_address": "127.0.0.1",

        "user_agent": "pytest",

    }
