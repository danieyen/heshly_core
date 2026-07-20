from __future__ import annotations

from heshly_core.models.workflow_template import (
    WorkflowStep,
    WorkflowTemplate,
)


class WorkflowTemplates:
    """
    Industry Workflow Templates.
    """

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

    def load(
        self,
        industry: str,
    ) -> WorkflowTemplate:

        templates = {

            "dental": self.dental,

            "salon": self.salon,

            "insurance": self.insurance,

            "logistics": self.logistics,

        }

        loader = templates.get(
            industry.lower()
        )

        if loader is None:

            raise ValueError(
                f"Unknown industry: {industry}"
            )

        return loader()