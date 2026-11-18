from __future__ import annotations

import frappe

from heshly_core.models.payment import (
    Payment,
    PaymentStatus,
    PaymentProvider,
)


class FrappePaymentRepository:

    DOCTYPE = "Heshly Payment"


    def current_tenant(self):
        from heshly_core.services.tenant.tenant_context import (
            TenantContext,
        )

        tenant = TenantContext().get()

        if not tenant:
            raise RuntimeError(
                "No active tenant context."
            )

        return tenant


    def save(
        self,
        payment: Payment,
    ) -> Payment:

        tenant_id = self.current_tenant()

        existing = frappe.db.exists(
            self.DOCTYPE,
            payment.payment_id,
        )

        if existing:
            doc = frappe.get_doc(
                self.DOCTYPE,
                payment.payment_id,
            )
        else:
            doc = frappe.new_doc(
                self.DOCTYPE
            )

            doc.payment_id = (
                payment.payment_id
            )


        doc.tenant_id = tenant_id
        doc.business_id = payment.business_id
        doc.subscription_id = payment.subscription_id

        doc.provider = (
            payment.provider.value.title()
        )

        doc.amount = payment.amount
        doc.currency = payment.currency

        doc.status = (
            payment.status.value.title()
        )

        doc.provider_reference = (
            payment.provider_reference
        )

        doc.completed_at = (
            payment.completed_at
        )

        doc.save()

        return self.get(
            payment.payment_id
        )


    def get(
        self,
        payment_id: str,
    ) -> Payment | None:

        tenant_id = self.current_tenant()

        row = frappe.db.get_value(
            self.DOCTYPE,
            {
                "payment_id": payment_id,
                "tenant_id": tenant_id,
            },
            [
                "payment_id",
                "tenant_id",
                "business_id",
                "subscription_id",
                "provider",
                "amount",
                "currency",
                "status",
                "provider_reference",
                "completed_at",
            ],
            as_dict=True,
        )

        if not row:
            return None

        return self._row_to_model(row)


    def all_for_business(
        self,
        business_id: str,
    ) -> list[Payment]:

        tenant_id = self.current_tenant()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "tenant_id": tenant_id,
                "business_id": business_id,
            },
            fields=[
                "payment_id",
                "tenant_id",
                "business_id",
                "subscription_id",
                "provider",
                "amount",
                "currency",
                "status",
                "provider_reference",
                "completed_at",
            ],
            order_by="creation desc",
        )

        return [
            self._row_to_model(row)
            for row in rows
        ]


    def _row_to_model(
        self,
        row,
    ) -> Payment:

        return Payment(
            payment_id=row.payment_id,
            tenant_id=row.tenant_id,
            business_id=row.business_id,
            subscription_id=row.subscription_id,
            provider=PaymentProvider(
                row.provider.lower()
            ),
            amount=row.amount,
            currency=row.currency,
            status=PaymentStatus(
                row.status.lower()
            ),
            provider_reference=row.provider_reference,
            completed_at=row.completed_at,
        )
