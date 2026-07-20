from datetime import time


class ScheduleKnowledge:
    """
    Provides business schedule knowledge.
    """

    def __init__(
        self,
        opening_time: time = time(8, 0),
        closing_time: time = time(17, 0),
        working_days: list[str] | None = None,
    ):
        self.opening_time = opening_time
        self.closing_time = closing_time
        self.working_days = working_days or [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
        ]

    def is_working_day(self, day: str) -> bool:
        return day in self.working_days

    def is_open_at(self, value: time) -> bool:
        return self.opening_time <= value <= self.closing_time

    def hours(self) -> tuple[time, time]:
        return self.opening_time, self.closing_time

    def days(self) -> list[str]:
        return self.working_days