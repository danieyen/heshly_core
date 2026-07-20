from __future__ import annotations

import json
import time
from copy import deepcopy
from datetime import UTC, datetime

from heshly_core.models.reporting import (
    ReportRequest,
    ReportResult,
    ReportStatus,
)


class ReportBuilder:
    """
    Generic Report Builder

    Responsible for converting analytics data into
    standardized report objects that can later be
    exported as JSON, CSV, Excel, PDF, or HTML.
    """

    def __init__(self):

        self.version = "1.0"

    # =====================================================
    # Build Report
    # =====================================================

    def build(
        self,
        request: ReportRequest,
        data: dict,
    ) -> ReportResult:

        started = time.perf_counter()

        report_data = deepcopy(data)

        rows = self._count_rows(report_data)

        elapsed = (
            time.perf_counter() - started
        ) * 1000

        return ReportResult(

            report_id=request.report_id,

            generated_at=datetime.now(
                UTC
            ),

            status=ReportStatus.COMPLETED,

            rows=rows,

            execution_time_ms=round(
                elapsed,
                2,
            ),

            data=report_data,

            metadata={

                "business_id":
                    request.business_id,

                "report_type":
                    request.report_type.value,

                "period":
                    request.period.value,

                "format":
                    request.output_format.value,

                "generated_by":
                    request.requested_by,

                "builder_version":
                    self.version,

            },

        )

    # =====================================================
    # Preview
    # =====================================================

    def preview(
        self,
        data: dict,
        limit: int = 10,
    ) -> dict:

        preview = {}

        for key, value in data.items():

            if isinstance(
                value,
                list,
            ):

                preview[key] = value[
                    :limit
                ]

            else:

                preview[key] = value

        return preview

    # =====================================================
    # Pretty JSON
    # =====================================================

    def to_json(
        self,
        report: ReportResult,
    ) -> str:

        return json.dumps(

            {

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

            },

            indent=4,

            default=str,

        )

    # =====================================================
    # Report Summary
    # =====================================================

    def summary(
        self,
        report: ReportResult,
    ) -> dict:

        return {

            "report_id":
                report.report_id,

            "status":
                report.status.value,

            "rows":
                report.rows,

            "generated_at":
                report.generated_at,

            "execution_time_ms":
                report.execution_time_ms,

            "metadata":
                report.metadata,

        }

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        request: ReportRequest,
    ) -> bool:

        if not request.report_id:
            return False

        if not request.business_id:
            return False

        if request.report_type is None:
            return False

        return True

    # =====================================================
    # Helpers
    # =====================================================

    def _count_rows(
        self,
        obj,
    ) -> int:

        if isinstance(
            obj,
            list,
        ):
            return len(obj)

        if isinstance(
            obj,
            dict,
        ):

            count = 0

            for value in obj.values():

                if isinstance(
                    value,
                    list,
                ):
                    count += len(value)

                elif isinstance(
                    value,
                    dict,
                ):
                    count += self._count_rows(
                        value
                    )

                else:
                    count += 1

            return count

        return 1