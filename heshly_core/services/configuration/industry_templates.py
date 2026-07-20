from __future__ import annotations

from heshly_core.models.tenant_configuration import (
    TenantConfiguration,
)


class IndustryTemplates:
    """
    Industry Template Library.

    Provides default configuration
    for supported industries.
    """

    def dental_clinic(self) -> TenantConfiguration:

        config = TenantConfiguration(
            tenant_id="template"
        )

        config.set("industry", "Dental Clinic")
        config.set("appointment_duration", 30)
        config.set("currency", "KES")
        config.set("timezone", "Africa/Nairobi")
        config.set("appointment_reminders", True)
        config.set("follow_up_enabled", True)

        return config

    def salon(self) -> TenantConfiguration:

        config = TenantConfiguration(
            tenant_id="template"
        )

        config.set("industry", "Salon")
        config.set("appointment_duration", 60)
        config.set("staff_assignment", True)
        config.set("loyalty_program", True)
        config.set("timezone", "Africa/Nairobi")

        return config

    def real_estate(self) -> TenantConfiguration:

        config = TenantConfiguration(
            tenant_id="template"
        )

        config.set("industry", "Real Estate")
        config.set("lead_qualification", True)
        config.set("property_pipeline", True)
        config.set("timezone", "Africa/Nairobi")

        return config

    def logistics(self) -> TenantConfiguration:

        config = TenantConfiguration(
            tenant_id="template"
        )

        config.set("industry", "Logistics")
        config.set("shipment_tracking", True)
        config.set("driver_assignment", True)
        config.set("notifications", True)

        return config

    def insurance(self) -> TenantConfiguration:

        config = TenantConfiguration(
            tenant_id="template"
        )

        config.set("industry", "Insurance")
        config.set("lead_qualification", True)
        config.set("renewal_reminders", True)
        config.set("quote_workflow", True)

        return config

    # ==========================================
    # Factory
    # ==========================================

    def load(
        self,
        industry: str,
    ) -> TenantConfiguration:

        templates = {

            "dental": self.dental_clinic,

            "salon": self.salon,

            "real_estate": self.real_estate,

            "logistics": self.logistics,

            "insurance": self.insurance,

        }

        loader = templates.get(
            industry.lower()
        )

        if loader is None:

            raise ValueError(
                f"Unknown industry: {industry}"
            )

        return loader()