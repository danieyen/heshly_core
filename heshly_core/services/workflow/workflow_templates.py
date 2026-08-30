from __future__ import annotations

import json
from typing import Any

from heshly_core.models.workflow_template import (
    WorkflowStep,
    WorkflowTemplate,
)

def _parse_json_string(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return value
        if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")):
            try:
                return json.loads(v)
            except Exception:
                return value
    return value


class WorkflowTemplates:
    """
    Industry Workflow Templates.
    Tolerant to n8n wrapping and case variations.
    """

    SUPPORTED_INDUSTRIES = {"dental", "salon", "insurance", "logistics"}

    def dental(self) -> WorkflowTemplate:

        template = WorkflowTemplate(

            template_id="dental",

            name="Dental Workflow",

            industry="Dental",

        )

        template.add_step(
            WorkflowStep(
                "1",
                "Receive Inquiry",
                "receive_message",
                1,
            )
        )

        template.add_step(
            WorkflowStep(
                "2",
                "Qualify Patient",
                "qualify_customer",
                2,
            )
        )

        template.add_step(
            WorkflowStep(
                "3",
                "Book Appointment",
                "book_appointment",
                3,
            )
        )

        template.add_step(
            WorkflowStep(
                "4",
                "Send Reminder",
                "send_reminder",
                4,
            )
        )

        return template

    def salon(self) -> WorkflowTemplate:

        template = WorkflowTemplate(

            template_id="salon",

            name="Salon Workflow",

            industry="Salon",

        )

        template.add_step(
            WorkflowStep(
                "1",
                "Receive Booking",
                "receive_booking",
                1,
            )
        )

        template.add_step(
            WorkflowStep(
                "2",
                "Assign Stylist",
                "assign_staff",
                2,
            )
        )

        template.add_step(
            WorkflowStep(
                "3",
                "Appointment Reminder",
                "send_reminder",
                3,
            )
        )

        return template

    def insurance(self) -> WorkflowTemplate:

        template = WorkflowTemplate(

            template_id="insurance",

            name="Insurance Workflow",

            industry="Insurance",

        )

        template.add_step(
            WorkflowStep(
                "1",
                "Capture Lead",
                "capture_lead",
                1,
            )
        )

        template.add_step(
            WorkflowStep(
                "2",
                "Qualify Lead",
                "qualify_lead",
                2,
            )
        )

        template.add_step(
            WorkflowStep(
                "3",
                "Generate Quote",
                "generate_quote",
                3,
            )
        )

        return template

    def logistics(self) -> WorkflowTemplate:

        template = WorkflowTemplate(

            template_id="logistics",

            name="Logistics Workflow",

            industry="Logistics",

        )

        template.add_step(
            WorkflowStep(
                "1",
                "Receive Order",
                "receive_order",
                1,
            )
        )

        template.add_step(
            WorkflowStep(
                "2",
                "Assign Driver",
                "assign_driver",
                2,
            )
        )

        template.add_step(
            WorkflowStep(
                "3",
                "Track Shipment",
                "track_shipment",
                3,
            )
        )

        return template

    def list_industries(self) -> list[str]:
        return sorted(self.SUPPORTED_INDUSTRIES)

    def is_supported(self, industry: Any) -> bool:
        if isinstance(industry, dict):
            # handle n8n dict payload
            for k in ("industry", "industry_type", "industryType", "template_id", "templateId"):
                if k in industry and isinstance(industry[k], str) and industry[k].strip():
                    industry = industry[k]
                    break
        if isinstance(industry, str):
            parsed = _parse_json_string(industry)
            if isinstance(parsed, dict):
                for k in ("industry", "industry_type"):
                    if k in parsed and isinstance(parsed[k], str):
                        industry = parsed[k]
                        break
        if not isinstance(industry, str) or not industry.strip():
            return False
        return industry.strip().lower() in self.SUPPORTED_INDUSTRIES

    def load(
        self,
        industry: str | dict | Any,
    ) -> WorkflowTemplate:
        if isinstance(industry, dict):
            # tolerant: extract from dict payload
            for k in ("industry", "industry_type", "industryType", "template_id", "templateId", "workflow_id"):
                if k in industry and isinstance(industry[k], str) and industry[k].strip():
                    industry = industry[k]
                    break
            # handle $json wrapping
            if isinstance(industry, dict):
                for wrap in ("$json", "json", "body", "data"):
                    if wrap in industry and isinstance(industry[wrap], dict):
                        inner = industry[wrap]
                        for k in ("industry", "industry_type"):
                            if k in inner and isinstance(inner[k], str):
                                industry = inner[k]
                                break
        if isinstance(industry, str):
            parsed = _parse_json_string(industry)
            if isinstance(parsed, dict):
                for k in ("industry", "industry_type", "template_id"):
                    if k in parsed and isinstance(parsed[k], str):
                        industry = parsed[k]
                        break
        if not isinstance(industry, str) or not industry.strip():
            raise ValueError("industry must be a non-empty string")

        normalized = industry.strip().lower()

        templates = {

            "dental": self.dental,

            "salon": self.salon,

            "insurance": self.insurance,

            "logistics": self.logistics,

        }

        loader = templates.get(
            normalized
        )

        if loader is None:

            raise ValueError(
                f"Unknown industry: {industry}. Supported: {', '.join(sorted(templates.keys()))}"
            )

        return loader()
