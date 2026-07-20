from heshly_core.models.session import (
    UserSession,
)
from heshly_core.services.security.jwt_manager import (
    JWTManager,
)
from heshly_core.services.security.refresh_token_manager import (
    RefreshTokenManager,
)
from heshly_core.services.security.token_manager import (
    TokenManager,
)
from heshly_core.services.security.token_revocation import (
    TokenRevocation,
)


def run_test():

    print("\n================================")
    print("Session & Token Security Test")
    print("================================\n")

    # =====================================================
    # Services
    # =====================================================

    token_manager = TokenManager()

    jwt_manager = JWTManager(
        secret="heshly-secret-key"
    )

    refresh_manager = RefreshTokenManager()

    revocation = TokenRevocation()

    print("✅ Services initialized")

    # =====================================================
    # User Session
    # =====================================================

    session = UserSession(

        user_id="user001",

        tenant_id="tenant001",

        ip_address="192.168.1.10",

        user_agent="Chrome",

    )

    assert session.is_active

    print("✅ Session created")

    session.touch()

    session.extend()

    assert session.is_active

    print("✅ Session updated")

    # =====================================================
    # Access Token
    # =====================================================

    access_token = token_manager.create_access_token(

        user_id="user001",

        tenant_id="tenant001",

    )

    assert token_manager.validate_access_token(
        access_token
    )

    print("✅ Access token")

    # =====================================================
    # Refresh Token
    # =====================================================

    refresh = refresh_manager.issue(

        user_id="user001",

        tenant_id="tenant001",

        session_id=session.session_id,

    )

    assert refresh_manager.validate(
        refresh.token
    )

    print("✅ Refresh token")

    replacement = refresh_manager.rotate(
        refresh.token
    )

    assert replacement is not None

    assert refresh_manager.validate(
        replacement.token
    )

    assert not refresh_manager.validate(
        refresh.token
    )

    print("✅ Refresh rotation")

    # =====================================================
    # JWT
    # =====================================================

    jwt = jwt_manager.create_token(

        user_id="user001",

        tenant_id="tenant001",

    )

    assert jwt_manager.validate(
        jwt
    )

    payload = jwt_manager.payload(
        jwt
    )

    assert payload["sub"] == "user001"

    print("✅ JWT support")

    # =====================================================
    # Token Revocation
    # =====================================================

    revocation.revoke(

        token=access_token,

        user_id="user001",

        tenant_id="tenant001",

        reason="Logout",

    )

    assert revocation.is_revoked(
        access_token
    )

    print("✅ Token revocation")

    # =====================================================
    # Session Revocation
    # =====================================================

    session.revoke()

    assert session.is_revoked

    print("✅ Session revoked")

    # =====================================================
    # Health
    # =====================================================

    assert (
        token_manager.health()["status"]
        ==
        "healthy"
    )

    assert (
        jwt_manager.health()["status"]
        ==
        "healthy"
    )

    assert (
        refresh_manager.health()["status"]
        ==
        "healthy"
    )

    assert (
        revocation.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health checks")

    print(
        "\n🎉 SESSION & TOKEN SECURITY TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()