from heshly_core.services.integration.authentication_integration import (
    AuthenticationIntegration,
)


class FakeUser:

    def __init__(self):

        self.user_id = "user001"



class FakeAuthenticationService:

    def authenticate(
        self,
        username,
        password,
    ):

        if username == "dan" and password == "password":

            return FakeUser()

        return None



class FakeLoginManager:
    pass



class FakeSessionManager:

    def __init__(self):

        self.sessions = {}


    def create(
        self,
        user_id,
        tenant_id=None,
    ):

        session = {

            "session_id": "session001",

            "user_id": user_id,

            "tenant_id": tenant_id,

        }

        self.sessions["session001"] = session

        return session


    def revoke(
        self,
        session_id,
    ):

        self.sessions.pop(
            session_id,
            None,
        )



class FakeTokenManager:

    def create(
        self,
        user_id,
    ):

        return "access_token"



class FakeJWTManager:

    def create(
        self,
        user_id,
    ):

        return "jwt_token"


    def verify(
        self,
        token,
    ):

        return {

            "user_id": "user001"

        }



class FakeRefreshTokenManager:

    def create(
        self,
        user_id,
    ):

        return "refresh_token"


    def validate(
        self,
        token,
    ):

        if token == "refresh_token":

            return "user001"

        return None


    def rotate(
        self,
        token,
    ):

        return "new_refresh_token"



class FakeTokenRevocation:

    def __init__(self):

        self.revoked = []


    def revoke(
        self,
        token,
    ):

        self.revoked.append(
            token
        )


    def is_revoked(
        self,
        token,
    ):

        return token in self.revoked



class FakeBruteForceProtection:

    def is_blocked(
        self,
        username,
    ):

        return False


    def record_failure(
        self,
        username,
    ):

        pass


    def reset(
        self,
        username,
    ):

        pass



class FakeAccountLockout:

    def is_locked(
        self,
        username,
    ):

        return False



class FakeAuditService:

    def login(
        self,
        **kwargs,
    ):

        pass


    def logout(
        self,
        **kwargs,
    ):

        pass



class FakeMetrics:

    def increment(
        self,
        name,
    ):

        pass



def run_test():

    print("\n================================")
    print("Authentication Integration Test")
    print("================================\n")


    integration = AuthenticationIntegration(

        authentication_service=FakeAuthenticationService(),

        login_manager=FakeLoginManager(),

        session_manager=FakeSessionManager(),

        token_manager=FakeTokenManager(),

        jwt_manager=FakeJWTManager(),

        refresh_token_manager=FakeRefreshTokenManager(),

        token_revocation=FakeTokenRevocation(),

        brute_force_protection=FakeBruteForceProtection(),

        account_lockout=FakeAccountLockout(),

        audit_service=FakeAuditService(),

        security_metrics=FakeMetrics(),

    )


    print("✅ Services initialized")


    result = integration.login(

        username="dan",

        password="password",

        tenant_id="tenant001",

    )


    assert result.success

    assert result.user.user_id == "user001"

    assert result.access_token == "access_token"

    assert result.refresh_token == "refresh_token"

    assert result.jwt == "jwt_token"


    print("✅ Login flow")


    validated = integration.validate_request(

        "jwt_token"

    )


    assert validated["user_id"] == "user001"


    print("✅ Token validation")


    refreshed = integration.refresh(

        "refresh_token"

    )


    assert refreshed["access_token"] == "access_token"

    assert refreshed["refresh_token"] == "new_refresh_token"


    print("✅ Token refresh")


    logout = integration.logout(

        user_id="user001",

        session_id="session001",

        token="jwt_token",

        tenant_id="tenant001",

    )


    assert logout["success"]


    print("✅ Logout")


    assert (
        integration.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health")


    print(
        "\n🎉 AUTHENTICATION INTEGRATION TEST PASSED\n"
    )



if __name__ == "__main__":

    run_test()