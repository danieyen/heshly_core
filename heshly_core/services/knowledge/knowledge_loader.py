import frappe

from heshly_core.models.knowledge import (
    BusinessProfile,
    KnowledgeContext,
)


class KnowledgeLoader:
    """
    Loads business knowledge from ERPNext.
    """

    def load(self) -> KnowledgeContext:

        context = KnowledgeContext()

        company = frappe.db.get_value(
            "Company",
            {},
            ["company_name", "default_currency"],
            as_dict=True,
        )

        if company:
            context.business = BusinessProfile(
                business_name=company.company_name,
                currency=company.default_currency,
            )

        return context