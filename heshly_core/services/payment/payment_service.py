from __future__ import annotations

from datetime import datetime

from heshly_core.models.payment import (
    Payment,
    PaymentProvider,
    PaymentStatus,
)

from heshly_core.repositories.frappe_payment_repository import (
    FrappePaymentRepository,
)

from heshly_core.services.subscription.subscription_service import (
    SubscriptionService,
)

from heshly_core.services.payment.providers.provider_factory import (
    PaymentProviderFactory,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class PaymentService:

    def __init__(
        self,
        repository: FrappePaymentRepository | None = None,
        subscription_service: SubscriptionService | None = None,
        tenant_context: TenantContext | None = None,
    ):
        self.repository = (
            repository
            or FrappePaymentRepository()
        )

        self.subscription_service = (
            subscription_service
            or SubscriptionService()
        )

        self.tenant_context = (
            tenant_context
            or TenantContext()
        )

    def create_payment(
        self,
        payment_id: str,
        business_id: str,
        subscription_id: str,
        provider: PaymentProvider,
        amount: float,
        currency: str = "USD",
    ) -> Payment:

        tenant_id = self.tenant_context.get()

        if not tenant_id:
            raise RuntimeError(
                "No active tenant context."
            )

        payment = Payment(
            payment_id=payment_id,
            tenant_id=tenant_id,
            business_id=business_id,
            subscription_id=subscription_id,
            provider=provider,
            amount=amount,
            currency=currency,
        )

        payment = self.repository.save(payment)

        gateway = PaymentProviderFactory.create(
            payment.provider
        )

        gateway.initiate_payment(payment)

        return payment

    def get_payment(
        self,
        payment_id: str,
    ) -> Payment | None:

        return self.repository.get(payment_id)

    def mark_success(
        self,
        payment_id: str,
        provider_reference: str | None = None,
    ) -> Payment:

        payment = self.get_payment(payment_id)

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        payment.status = PaymentStatus.SUCCESS
        payment.provider_reference = provider_reference
        payment.completed_at = datetime.utcnow()

        payment = self.repository.save(payment)

        self.subscription_service.activate_subscription(
            payment.business_id
        )

        return payment

    def mark_failed(
        self,
        payment_id: str,
    ) -> Payment:

        payment = self.get_payment(payment_id)

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        payment.status = PaymentStatus.FAILED

        return self.repository.save(payment)

    def refund(
        self,
        payment_id: str,
    ) -> Payment:

        payment = self.get_payment(payment_id)

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        payment.status = PaymentStatus.REFUNDED

        return self.repository.save(payment)
