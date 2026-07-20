from __future__ import annotations

from heshly_core.services.integration.service_container import (
    ServiceContainer,
)


class DummyService:
    def __init__(self, name: str):
        self.name = name

    def health(self):
        return {
            "status": "healthy"
        }


def test_module_integration():

    print("\n================================")
    print("Module Integration Test")
    print("================================\n")

    ai = DummyService("AI")
    calendar = DummyService("Calendar")
    crm = DummyService("CRM")
    analytics = DummyService("Analytics")
    reporting = DummyService("Reporting")
    security = DummyService("Security")

    container = ServiceContainer(

        ai=ai,

        calendar=calendar,

        crm=crm,

        analytics=analytics,

        reporting=reporting,

        security=security,

    )

    # ==========================================
    # Registration
    # ==========================================

    assert container.has("ai")
    assert container.has("calendar")
    assert container.has("crm")
    assert container.has("analytics")
    assert container.has("reporting")
    assert container.has("security")

    print("✅ Registration")

    # ==========================================
    # Retrieval
    # ==========================================

    assert container.get("ai") is ai
    assert container.get("calendar") is calendar
    assert container.get("crm") is crm
    assert container.get("analytics") is analytics
    assert container.get("reporting") is reporting
    assert container.get("security") is security

    print("✅ Retrieval")

    # ==========================================
    # Registry
    # ==========================================

    assert len(container.names()) == 6
    assert len(container.services()) == 6

    print("✅ Registry")

    # ==========================================
    # Health
    # ==========================================

    health = container.health()

    assert health["status"] == "healthy"
    assert len(health["services"]) == 6

    print("✅ Health")

    print("\n🎉 MODULE INTEGRATION TEST PASSED\n")