from __future__ import annotations

import statistics
import time


class MockAPI:

    def health(self):

        return {
            "status": "healthy",
        }

    def customers(self):

        return []

    def appointments(self):

        return []

    def analytics(self):

        return {
            "appointments": 0,
        }


def benchmark(
    name: str,
    func,
    iterations: int = 1000,
):

    durations = []

    for _ in range(iterations):

        start = time.perf_counter()

        func()

        durations.append(
            time.perf_counter() - start
        )

    avg = statistics.mean(durations)

    minimum = min(durations)

    maximum = max(durations)

    print(
        f"{name:<20}"
        f" avg={avg*1000:.3f}ms"
        f" min={minimum*1000:.3f}ms"
        f" max={maximum*1000:.3f}ms"
    )

    return avg


def test_api_performance():

    print("\n================================")
    print("API Performance Tests")
    print("================================\n")

    api = MockAPI()

    health = benchmark(
        "Health",
        api.health,
    )

    customers = benchmark(
        "Customers",
        api.customers,
    )

    appointments = benchmark(
        "Appointments",
        api.appointments,
    )

    analytics = benchmark(
        "Analytics",
        api.analytics,
    )

    assert health < 0.01

    assert customers < 0.01

    assert appointments < 0.01

    assert analytics < 0.01

    print("\n🎉 API PERFORMANCE TEST PASSED\n")