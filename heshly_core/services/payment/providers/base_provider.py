from abc import ABC, abstractmethod

from heshly_core.models.payment import Payment


class PaymentProviderBase(ABC):

    @abstractmethod
    def initiate_payment(self, payment: Payment):
        pass

    @abstractmethod
    def verify_payment(self, provider_reference: str):
        pass

    @abstractmethod
    def refund(self, payment: Payment):
        pass
