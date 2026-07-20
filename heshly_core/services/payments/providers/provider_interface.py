from __future__ import annotations

from abc import ABC, abstractmethod

from heshly_core.services.payments.providers.provider_models import (
    ProviderCapabilities,
    ProviderConfiguration,
    ProviderInfo,
    ProviderPaymentRequest,
    ProviderPaymentResult,
    ProviderRefundRequest,
    ProviderRefundResult,
)


class PaymentProviderInterface(ABC):
    """
    Base interface for all payment providers.
    """

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """
        Returns provider metadata.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def configuration(self) -> ProviderConfiguration:
        """
        Returns provider configuration.
        """
        raise NotImplementedError

    @property
    def capabilities(self) -> ProviderCapabilities:
        """
        Returns provider capabilities.
        """
        return self.info.capabilities

    @abstractmethod
    def process_payment(
        self,
        request: ProviderPaymentRequest,
    ) -> ProviderPaymentResult:
        """
        Process a payment request.
        """
        raise NotImplementedError

    @abstractmethod
    def verify_payment(
        self,
        transaction_id: str,
    ) -> ProviderPaymentResult:
        """
        Verify a payment with the provider.
        """
        raise NotImplementedError

    @abstractmethod
    def refund(
        self,
        request: ProviderRefundRequest,
    ) -> ProviderRefundResult:
        """
        Process a refund.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(
        self,
    ) -> bool:
        """
        Check provider availability.
        """
        raise NotImplementedError