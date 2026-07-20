from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from heshly_core.models.reporting import (
    ReportExport,
    ReportFormat,
    ReportResult,
)


class ExportEngine:
    """
    Report Export Engine

    Supports exporting reports to:

    • JSON
    • CSV
    • HTML

    (PDF/XLSX exporters can be added later.)
    """

    def __init__(
        self,
        export_directory: str = "exports",
    ):

        self.export_directory = Path(
            export_directory
        )

        self.export_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =====================================================
    # Export
    # =====================================================

    def export(
        self,
        report: ReportResult,
        output_format: ReportFormat,
    ) -> ReportExport:

        if output_format == ReportFormat.JSON:
            path = self.export_json(report)

        elif output_format == ReportFormat.CSV:
            path = self.export_csv(report)

        elif output_format == ReportFormat.HTML:
            path = self.export_html(report)

        else:
            raise ValueError(
                f"Unsupported export format: {output_format}"
            )

        return ReportExport(

            export_id=f"EXP-{report.report_id}",

            report_id=report.report_id,

            format=output_format,

            filename=path.name,

            created_at=datetime.now(
                UTC
            ),

            file_size=path.stat().st_size,

            download_url=str(path),

        )

    # =====================================================
    # JSON
    # =====================================================

    def export_json(
        self,
        report: ReportResult,
    ) -> Path:

        filename = (
            self.export_directory
            / f"{report.report_id}.json"
        )

        payload = {

            "report_id":
                report.report_id,

            "generated_at":
                report.generated_at.isoformat(),

            "status":
                report.status.value,

            "rows":
                report.rows,

            "execution_time_ms":
                report.execution_time_ms,

            "metadata":
                report.metadata,

            "data":
                report.data,

        }

        with open(
            filename,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                payload,
                f,
                indent=4,
                default=str,
            )

        return filename

    # =====================================================
    # CSV
    # =====================================================

    def export_csv(
        self,
        report: ReportResult,
    ) -> Path:

        filename = (
            self.export_directory
            / f"{report.report_id}.csv"
        )

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8",
        ) as f:

            writer = csv.writer(f)

            writer.writerow(
                [
                    "Section",
                    "Key",
                    "Value",
                ]
            )

            self._write_dict(
                writer,
                "",
                report.data,
            )

        return filename

    # =====================================================
    # HTML
    # =====================================================

    def export_html(
        self,
        report: ReportResult,
    ) -> Path:

        filename = (
            self.export_directory
            / f"{report.report_id}.html"
        )

        html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{report.report_id}</title>

<style>

body {{
    font-family: Arial, sans-serif;
    margin:40px;
}}

table {{
    border-collapse: collapse;
    width:100%;
}}

th, td {{
    border:1px solid #ddd;
    padding:8px;
}}

th {{
    background:#efefef;
}}

</style>

</head>

<body>

<h1>{report.report_id}</h1>

<p>
Generated:
{report.generated_at}
</p>

<pre>
{json.dumps(report.data, indent=4, default=str)}
</pre>

</body>

</html>
"""

        filename.write_text(
            html,
            encoding="utf-8",
        )

        return filename

    # =====================================================
    # Helpers
    # =====================================================

    def _write_dict(
        self,
        writer,
        prefix,
        value,
    ):

        if isinstance(
            value,
            dict,
        ):

            for k, v in value.items():

                key = (
                    f"{prefix}.{k}"
                    if prefix
                    else k
                )

                self._write_dict(
                    writer,
                    key,
                    v,
                )

        elif isinstance(
            value,
            list,
        ):

            writer.writerow(
                [
                    prefix,
                    "items",
                    len(value),
                ]
            )

            for i, item in enumerate(value):

                self._write_dict(
                    writer,
                    f"{prefix}[{i}]",
                    item,
                )

        else:

            writer.writerow(
                [
                    "",
                    prefix,
                    value,
                ]
            )