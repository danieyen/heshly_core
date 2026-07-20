"""
Performance measurement helpers.
"""

import time



class Timer:

    def __init__(self):

        self.start_time = None

        self.end_time = None



    def start(self):

        self.start_time = time.perf_counter()



    def stop(self):

        self.end_time = time.perf_counter()



    @property
    def elapsed(self):

        if not self.start_time:
            return 0

        end = (
            self.end_time
            or
            time.perf_counter()
        )

        return end - self.start_time
