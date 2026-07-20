from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor


class MockBookingService:

    def book(
        self,
        customer_id: str,
    ) -> bool:

        return True


def worker(
    service: MockBookingService,
    index: int,
) -> bool:

    return service.book(
        f"CUST-{index}",
    )


def test_load_testing():

    print("\n================================")
    print("Load Testing")
    print("================================\n")

    service = MockBookingService()

    total_requests = 1000

    start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=50,
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

    requests_per_second = total_requests / duration

    print(f"Requests      : {total_requests}")
    print(f"Successful    : {successful}")
    print(f"Duration      : {duration:.2f}s")
    print(f"Throughput    : {requests_per_second:.2f} req/sec")

    assert successful == total_requests

    print("\n🎉 LOAD TEST PASSED\n")