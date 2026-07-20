from __future__ import annotations

from pathlib import Path

from heshly_core.models.reporting import (
    ReportFormat,
    ReportRequest,
    ReportResult,
)
from heshly_core.services.reporting.report_builder import (
    ReportBuilder,
)
from heshly_core.services.reporting.scheduled_reports import (
    ScheduledReports,
)
from heshly_core.services.reporting.export_engine import (
    ExportEngine,
)
from heshly_core.services.reporting.pdf_report_generator import (
    PDFReportGenerator,
)
from heshly_core.services.reporting.excel_report_generator import (
    ExcelReportGenerator,
)
from heshly_core.services.reporting.email_reports import (
    EmailReports,
)


class ReportManager:
    """
    Central Reporting Manager

    Coordinates:

    • Report Builder
    • Scheduled Reports
    • Export Engine
    • PDF Reports
    • Excel Reports
    • Email Reports
    """

    def __init__(
        self,
        export_directory: str = "exports",
    ):

        self.builder = ReportBuilder()

        self.scheduler = ScheduledReports()

        self.exporter = ExportEngine(
            export_directory
        )

        self.pdf = PDFReportGenerator(
            export_directory
        )

        self.excel = ExcelReportGenerator(
            export_directory
        )

        self.email = EmailReports()

    # =====================================================
    # Build
    # =====================================================

    def build(
        self,
        request: ReportRequest,
        data: dict,
    ) -> ReportResult:

        return self.builder.build(
            request,
            data,
        )

    # =====================================================
    # Export
    # =====================================================

    def export(
        self,
        report: ReportResult,
        fmt: ReportFormat,
    ):

        return self.exporter.export(
            report,
            fmt,
        )

    # =====================================================
    # PDF
    # =====================================================

    def export_pdf(
        self,
        report: ReportResult,
    ) -> Path:

        return self.pdf.generate(
            report
        )

    # =====================================================
    # Excel
    # =====================================================

    def export_excel(
        self,
        report: ReportResult,
    ) -> Path:

        return self.excel.generate(
            report
        )

    # =====================================================
    # Email
    # =====================================================

    def email_report(
        self,
        recipient: str,
        report: ReportResult,
        attachment: str | Path | None = None,
        subject: str | None = None,
        body: str | None = None,
    ) -> bool:

        return self.email.send(

            recipient=recipient,

            report=report,

            attachment=attachment,

            subject=subject,

            body=body,

        )

    # =====================================================
    # Scheduler
    # =====================================================

    def scheduler_summary(
        self,
    ) -> dict:

        return self.scheduler.summary()

    # =====================================================
    # Report Summary
    # =====================================================

    def summary(
        self,
        report: ReportResult,
    ) -> dict:

        return self.builder.summary(
            report
        )

    # =====================================================
    # Health
    # =====================================================

    def health(
        self,
    ) -> dict:

        return {

            "status": "healthy",

            "services": {

                "report_builder": True,

                "scheduled_reports": True,

                "export_engine": True,

                "pdf_reports": True,

                "excel_reports": True,

                "email_reports": True,

                "report_manager": True,

            },

            "scheduler":
                self.scheduler.summary(),

            "email":
                self.email.health(),

        }