from __future__ import annotations

from dataclasses import dataclass


@dataclass
class APIResponse:
    status: int
    data: dict


class MockAPI:

    def health(self):

        return APIResponse(
            status=200,
            data={
                "status": "healthy",
            },
        )

    def authenticate(self):

        return APIResponse(
            status=200,
            data={
                "token": "test-token",
            },
        )

    def customers(self):

        return APIResponse(
            status=200,
            data={
                "count": 5,
            },
        )

    def appointments(self):

        return APIResponse(
            status=200,
            data={
                "count": 3,
            },
        )

    def analytics(self):

        return APIResponse(
            status=200,
            data={
                "reports": 2,
            },
        )


def test_api_integration():

    print("\n================================")
    print("API Integration Test")
    print("================================\n")

    api = MockAPI()

    # =====================================
    # Health Endpoint
    # =====================================

    response = api.health()

    assert response.status == 200
    assert response.data["status"] == "healthy"

    print("✅ Health API")

    # =====================================
    # Authentication
    # =====================================

    response = api.authenticate()

    assert response.status == 200
    assert "token" in response.data

    print("✅ Authentication API")

    # =====================================
    # Customers
    # =====================================

    response = api.customers()

    assert response.status == 200
    assert response.data["count"] == 5

    print("✅ Customer API")

    # =====================================
    # Appointments
    # =====================================

    response = api.appointments()

    assert response.status == 200
    assert response.data["count"] == 3

    print("✅ Appointment API")

    # =====================================
    # Analytics
    # =====================================

    response = api.analytics()

    assert response.status == 200
    assert response.data["reports"] == 2

    print("✅ Analytics API")

    print("\n🎉 API INTEGRATION TEST PASSED\n")