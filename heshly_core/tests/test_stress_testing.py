from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor


class MockBookingService:

    MAX_CAPACITY = 5000

    def book(
        self,
        customer_id: str,
    ) -> bool:

        # Simulate occasional failures under stress
        if random.random() < 0.02:
            return False

        return True


def worker(
    service: MockBookingService,
    index: int,
) -> bool:

    return service.book(
        f"CUSTOMER-{index}",
    )


def test_stress_testing():

    print("\n================================")
    print("Stress Testing")
    print("================================\n")

    service = MockBookingService()

    total_requests = 10000

    start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=200,
    ) as executor:

        results = list(

            executor.map(

                lambda i: worker(
                    service,
                    i,
                ),

                range(total_requests),

            )

        )

    duration = time.perf_counter() - start

    successful = sum(results)

    failed = total_requests - successful

    success_rate = (successful / total_requests) * 100

    throughput = total_requests / duration

    print(f"Requests       : {total_requests}")
    print(f"Successful     : {successful}")
    print(f"Failed         : {failed}")
    print(f"Success Rate   : {success_rate:.2f}%")
    print(f"Duration       : {duration:.2f}s")
    print(f"Throughput     : {throughput:.2f} req/sec")

    # System should survive heavy load
    assert success_rate >= 95

    print("\n🎉 STRESS TEST PASSED\n")