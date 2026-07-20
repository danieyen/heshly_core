from __future__ import annotations

from pathlib import Path

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

from heshly_core.models.reporting import ReportResult


class PDFReportGenerator:
    """
    Generates PDF reports from ReportResult objects.
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

        self.styles = getSampleStyleSheet()

    # =====================================================
    # Generate
    # =====================================================

    def generate(
        self,
        report: ReportResult,
    ) -> Path:

        filename = (
            self.output_directory /
            f"{report.report_id}.pdf"
        )

        document = SimpleDocTemplate(
            str(filename)
        )

        elements = []

        elements.append(
            Paragraph(
                f"<b>{report.report_id}</b>",
                self.styles["Title"],
            )
        )

        elements.append(
            Paragraph(
                f"Generated: {report.generated_at}",
                self.styles["Normal"],
            )
        )

        elements.append(
            Paragraph(
                f"Rows: {report.rows}",
                self.styles["Normal"],
            )
        )

        elements.append(
            Paragraph(
                f"Execution Time: {report.execution_time_ms} ms",
                self.styles["Normal"],
            )
        )

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                "<b>Metadata</b>",
                self.styles["Heading2"],
            )
        )

        metadata_table = [["Key", "Value"]]

        for key, value in report.metadata.items():

            metadata_table.append(
                [
                    str(key),
                    str(value),
                ]
            )

        table = Table(metadata_table)

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ]
            )
        )

        elements.append(table)

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                "<b>Report Data</b>",
                self.styles["Heading2"],
            )
        )

        self._append_dict(
            report.data,
            elements,
            level=0,
        )

        document.build(elements)

        return filename

    # =====================================================
    # Recursive Writer
    # =====================================================

    def _append_dict(
        self,
        data,
        elements,
        level=0,
    ):

        indent = "&nbsp;" * (level * 4)

        if isinstance(data, dict):

            for key, value in data.items():

                if isinstance(
                    value,
                    (dict, list),
                ):

                    elements.append(
                        Paragraph(
                            f"{indent}<b>{key}</b>",
                            self.styles["Heading3"],
                        )
                    )

                    self._append_dict(
                        value,
                        elements,
                        level + 1,
                    )

                else:

                    elements.append(
                        Paragraph(
                            f"{indent}{key}: {value}",
                            self.styles["Normal"],
                        )
                    )

        elif isinstance(data, list):

            for item in data:

                self._append_dict(
                    item,
                    elements,
                    level + 1,
                )