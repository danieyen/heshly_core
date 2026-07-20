from __future__ import annotations

import statistics
import time


class MockRepository:

    def __init__(self):

        self._data = {}

    def save(
        self,
        entity: dict,
    ):

        self._data[entity["id"]] = entity

        return entity

    def get(
        self,
        entity_id: str,
    ):

        return self._data.get(
            entity_id
        )

    def list(self):

        return list(
            self._data.values()
        )

    def delete(
        self,
        entity_id: str,
    ):

        self._data.pop(
            entity_id,
            None,
        )


def benchmark(
    name: str,
    func,
):

    timings = []

    for _ in range(1000):

        start = time.perf_counter()

        func()

        timings.append(
            time.perf_counter() - start
        )

    average = statistics.mean(
        timings
    )

    print(
        f"{name:<15}"
        f" avg={average*1000:.3f} ms"
    )

    return average


def test_database_performance():

    print("\n================================")
    print("Database Performance Tests")
    print("================================\n")

    repo = MockRepository()

    for i in range(1000):

        repo.save(
            {
                "id": str(i),
                "name": f"Customer {i}",
            }
        )

    save_time = benchmark(

        "SAVE",

        lambda: repo.save(
            {
                "id": "benchmark",
                "name": "Benchmark",
            }
        ),

    )

    get_time = benchmark(

        "GET",

        lambda: repo.get(
            "500",
        ),

    )

    list_time = benchmark(

        "LIST",

        repo.list,

    )

    delete_time = benchmark(

        "DELETE",

        lambda: repo.delete(
            "benchmark",
        ),

    )

    assert save_time < 0.01

    assert get_time < 0.01

    assert list_time < 0.01

    assert delete_time < 0.01

    print("\n🎉 DATABASE PERFORMANCE TEST PASSED\n")