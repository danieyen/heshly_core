from dataclasses import dataclass, field


@dataclass(slots=True)
class ServiceInfo:
    name: str
    description: str | None = None
    duration_minutes: int | None = None
    price: float | None = None
    active: bool = True


@dataclass(slots=True)
class StaffInfo:
    name: str
    role: str | None = None
    available: bool = True


@dataclass(slots=True)
class BusinessProfile:
    business_name: str
    timezone: str = "Africa/Nairobi"
    currency: str = "KES"


@dataclass(slots=True)
class FAQItem:
    question: str
    answer: str


@dataclass(slots=True)
class BusinessPolicy:
    key: str
    value: str


@dataclass(slots=True)
class KnowledgeContext:
    business: BusinessProfile | None = None
    services: list[ServiceInfo] = field(default_factory=list)
    staff: list[StaffInfo] = field(default_factory=list)
    faqs: list[FAQItem] = field(default_factory=list)
    policies: list[BusinessPolicy] = field(default_factory=list)