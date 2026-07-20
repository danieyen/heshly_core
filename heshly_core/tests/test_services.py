from heshly_core.services.integration.service_container import (
    ServiceContainer,
)


class HealthyService:

    def health(self):

        return {
            "status": "healthy",
        }


class UnknownService:

    pass


def test_service_container():

    print("\n================================")
    print("Service Tests")
    print("================================\n")

    container = ServiceContainer(

        service_a=HealthyService(),

        service_b=HealthyService(),

        service_c=UnknownService(),

    )

    # =====================================================
    # Registration
    # =====================================================

    assert container.has("service_a")

    assert container.has("service_b")

    assert container.has("service_c")

    assert not container.has("missing")

    print("✅ Registration")

    # =====================================================
    # Retrieval
    # =====================================================

    assert isinstance(
        container.get("service_a"),
        HealthyService,
    )

    assert container.get("missing") is None

    print("✅ Retrieval")

    # =====================================================
    # Names
    # =====================================================

    names = container.names()

    assert "service_a" in names

    assert "service_b" in names

    assert "service_c" in names

    print("✅ Names")

    # =====================================================
    # Services Dictionary
    # =====================================================

    services = container.services()

    assert len(services) == 3

    assert isinstance(
        services,
        dict,
    )

    print("✅ Dictionary")

    # =====================================================
    # Health
    # =====================================================

    health = container.health()

    assert health["service"] == "ServiceContainer"

    assert health["status"] == "degraded"

    assert health["services"]["service_a"] == "healthy"

    assert health["services"]["service_b"] == "healthy"

    assert health["services"]["service_c"] == "unknown"

    print("✅ Health")

    print("\n🎉 SERVICE TESTS PASSED\n")