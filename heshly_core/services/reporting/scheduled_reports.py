from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Dict

from heshly_core.models.reporting import (
    ScheduledReport,
)


class ScheduledReports:
    """
    Scheduled Report Manager

    Handles creation, scheduling and execution tracking
    of recurring reports.

    Supported frequencies
    ---------------------
    • hourly
    • daily
    • weekly
    • monthly (30 days)
    • quarterly (90 days)
    • yearly (365 days)
    """

    def __init__(self):

        self._reports: Dict[
            str,
            ScheduledReport,
        ] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def add(
        self,
        report: ScheduledReport,
    ) -> ScheduledReport:

        if report.next_run is None:
            report.next_run = datetime.now(
                UTC
            )

        self._reports[
            report.schedule_id
        ] = report

        return report

    def get(
        self,
        schedule_id: str,
    ) -> ScheduledReport | None:

        return self._reports.get(
            schedule_id
        )

    def list(self) -> list[ScheduledReport]:

        return list(
            self._reports.values()
        )

    def remove(
        self,
        schedule_id: str,
    ) -> bool:

        return (
            self._reports.pop(
                schedule_id,
                None,
            )
            is not None
        )

    # =====================================================
    # Enable / Disable
    # =====================================================

    def enable(
        self,
        schedule_id: str,
    ) -> bool:

        report = self.get(
            schedule_id
        )

        if report is None:
            return False

        report.enabled = True
        return True

    def disable(
        self,
        schedule_id: str,
    ) -> bool:

        report = self.get(
            schedule_id
        )

        if report is None:
            return False

        report.enabled = False
        return True

    # =====================================================
    # Scheduling
    # =====================================================

    def due_reports(
        self,
        now: datetime | None = None,
    ) -> list[ScheduledReport]:

        now = now or datetime.now(
            UTC
        )

        due = []

        for report in self._reports.values():

            if (
                report.enabled
                and report.next_run
                and report.next_run <= now
            ):
                due.append(report)

        return due

    def mark_completed(
        self,
        schedule_id: str,
        frequency: str = "daily",
    ) -> bool:

        report = self.get(
            schedule_id
        )

        if report is None:
            return False

        now = datetime.now(
            UTC
        )

        report.last_run = now
        report.next_run = (
            self._next_run(
                now,
                frequency,
            )
        )

        return True

    # =====================================================
    # Summary
    # =====================================================

    def summary(self) -> dict:

        enabled = sum(
            1
            for report in self._reports.values()
            if report.enabled
        )

        disabled = (
            len(self._reports)
            - enabled
        )

        due = len(
            self.due_reports()
        )

        return {

            "total_reports":
                len(self._reports),

            "enabled":
                enabled,

            "disabled":
                disabled,

            "due":
                due,

        }

    # =====================================================
    # Helpers
    # =====================================================

    def _next_run(
        self,
        current: datetime,
        frequency: str,
    ) -> datetime:

        frequency = frequency.lower()

        mapping = {

            "hourly":
                timedelta(hours=1),

            "daily":
                timedelta(days=1),

            "weekly":
                timedelta(weeks=1),

            "monthly":
                timedelta(days=30),

            "quarterly":
                timedelta(days=90),

            "yearly":
                timedelta(days=365),

        }

        delta = mapping.get(
            frequency,
            timedelta(days=1),
        )

        return current + delta