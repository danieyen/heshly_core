from __future__ import annotations

import queue
import statistics
import threading
import time


TOTAL_MESSAGES = 10000


def producer(q: queue.Queue):

    for i in range(TOTAL_MESSAGES):

        q.put(
            f"job-{i}"
        )


def consumer(q: queue.Queue):

    processed = 0

    while processed < TOTAL_MESSAGES:

        try:

            q.get(
                timeout=1,
            )

            q.task_done()

            processed += 1

        except queue.Empty:

            pass


def test_queue_performance():

    print("\n================================")
    print("Queue Performance Tests")
    print("================================\n")

    q = queue.Queue()

    start = time.perf_counter()

    producer_thread = threading.Thread(
        target=producer,
        args=(q,),
    )

    consumer_thread = threading.Thread(
        target=consumer,
        args=(q,),
    )

    producer_thread.start()

    consumer_thread.start()

    producer_thread.join()

    q.join()

    consumer_thread.join()

    elapsed = time.perf_counter() - start

    throughput = TOTAL_MESSAGES / elapsed

    print(f"Messages      : {TOTAL_MESSAGES}")
    print(f"Duration      : {elapsed:.3f}s")
    print(f"Throughput    : {throughput:.2f} msg/sec")
    print(f"Queue Empty   : {q.empty()}")

    assert q.empty()

    assert throughput > 1000

    print("\n🎉 QUEUE PERFORMANCE TEST PASSED\n")