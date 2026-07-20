from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from heshly_core.models.reporting import ReportResult


class ExcelReportGenerator:
    """
    Excel Report Generator

    Generates .xlsx reports from ReportResult objects.
    """

    def __init__(
        self,
        output_directory: str = "exports",
    ):

        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =====================================================
    # Generate
    # =====================================================

    def generate(
        self,
        report: ReportResult,
    ) -> Path:

        workbook = Workbook()

        metadata_sheet = workbook.active
        metadata_sheet.title = "Metadata"

        self._build_metadata_sheet(
            metadata_sheet,
            report,
        )

        data_sheet = workbook.create_sheet(
            "Data"
        )

        self._build_data_sheet(
            data_sheet,
            report.data,
        )

        filename = (
            self.output_directory
            / f"{report.report_id}.xlsx"
        )

        workbook.save(filename)

        return filename

    # =====================================================
    # Metadata Sheet
    # =====================================================

    def _build_metadata_sheet(
        self,
        sheet,
        report: ReportResult,
    ):

        sheet["A1"] = "Field"
        sheet["B1"] = "Value"

        sheet["A1"].font = Font(
            bold=True
        )

        sheet["B1"].font = Font(
            bold=True
        )

        row = 2

        values = {

            "Report ID":
                report.report_id,

            "Generated":
                str(report.generated_at),

            "Rows":
                report.rows,

            "Execution Time (ms)":
                report.execution_time_ms,

            "Status":
                report.status.value,

        }

        values.update(
            report.metadata
        )

        for key, value in values.items():

            sheet.cell(
                row=row,
                column=1,
                value=str(key),
            )

            sheet.cell(
                row=row,
                column=2,
                value=str(value),
            )

            row += 1

    # =====================================================
    # Data Sheet
    # =====================================================

    def _build_data_sheet(
        self,
        sheet,
        data,
    ):

        sheet["A1"] = "Key"
        sheet["B1"] = "Value"

        sheet["A1"].font = Font(
            bold=True
        )

        sheet["B1"].font = Font(
            bold=True
        )

        row = 2

        row = self._write(
            sheet=sheet,
            row=row,
            prefix="",
            value=data,
        )

        sheet.column_dimensions[
            "A"
        ].width = 45

        sheet.column_dimensions[
            "B"
        ].width = 60

    # =====================================================
    # Recursive Writer
    # =====================================================

    def _write(
        self,
        sheet,
        row: int,
        prefix: str,
        value,
    ) -> int:

        if isinstance(
            value,
            dict,
        ):

            for key, item in value.items():

                name = (
                    f"{prefix}.{key}"
                    if prefix
                    else key
                )

                row = self._write(
                    sheet,
                    row,
                    name,
                    item,
                )

            return row

        if isinstance(
            value,
            list,
        ):

            if not value:

                sheet.cell(
                    row=row,
                    column=1,
                    value=prefix,
                )

                sheet.cell(
                    row=row,
                    column=2,
                    value="[]",
                )

                return row + 1

            for index, item in enumerate(
                value
            ):

                row = self._write(
                    sheet,
                    row,
                    f"{prefix}[{index}]",
                    item,
                )

            return row

        sheet.cell(
            row=row,
            column=1,
            value=prefix,
        )

        sheet.cell(
            row=row,
            column=2,
            value=str(value),
        )

        return row + 1