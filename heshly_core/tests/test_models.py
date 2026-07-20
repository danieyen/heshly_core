from dataclasses import is_dataclass

from heshly_core.models.tenant import Tenant
from heshly_core.models.user import User
from heshly_core.models.auth import AuthUser
from heshly_core.models.session import UserSession
from heshly_core.models.api_key import APIKey
from heshly_core.models.audit_log import (
    AuditLog,
    AuditEventType,
)


def test_models():

    print("\n================================")
    print("Model Tests")
    print("================================\n")

    # =====================================================
    # Tenant
    # =====================================================

    tenant = Tenant(
        tenant_id="tenant001",
        name="Acme Ltd",
    )

    assert is_dataclass(tenant)
    assert tenant.tenant_id == "tenant001"
    assert tenant.name == "Acme Ltd"

    tenant.activate()
    assert tenant.is_active

    print("✅ Tenant")

    # =====================================================
    # User
    # =====================================================

    user = User(
        user_id="user001",
        tenant_id="tenant001",
        name="John Doe",
        email="john@example.com",
    )

    assert is_dataclass(user)
    assert user.is_active

    user.suspend()

    assert user.status == "suspended"

    print("✅ User")

    # =====================================================
    # Auth User
    # =====================================================

    auth = AuthUser(
        user_id="user001",
        email="john@example.com",
    )

    assert auth.is_active

    auth.record_login()

    assert auth.last_login is not None

    print("✅ AuthUser")

    # =====================================================
    # Session
    # =====================================================

    session = UserSession(
        user_id="user001",
        tenant_id="tenant001",
    )

    assert session.is_active

    session.revoke()

    assert session.is_revoked

    print("✅ Session")

    # =====================================================
    # API Key
    # =====================================================

    api_key = APIKey(
        key_id="key001",
        tenant_id="tenant001",
        name="Integration",
        key_hash="abc123",
    )

    assert api_key.is_active

    api_key.disable()

    assert not api_key.is_active

    print("✅ API Key")

    # =====================================================
    # Audit Log
    # =====================================================

    audit = AuditLog(
        audit_id="audit001",
        tenant_id="tenant001",
        user_id="user001",
        event_type=AuditEventType.SECURITY,
        action="login",
        resource="authentication",
    )

    assert audit.is_security_event
    assert not audit.is_failure

    print("✅ Audit Log")

    print("\n🎉 MODEL TESTS PASSED\n")