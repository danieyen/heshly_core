from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


# ==========================================================
# ENUMS
# ==========================================================

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class OpportunityStatus(str, Enum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"


class ActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class FollowUpStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"


# ==========================================================
# MODELS
# ==========================================================

@dataclass(slots=True)
class Lead:
    lead_id: str
    business_id: str
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None

    source: str = "whatsapp"

    status: LeadStatus = LeadStatus.NEW
    score: int = 0

    assigned_to: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class Opportunity:
    opportunity_id: str
    lead_id: str

    tenant_id: str

    title: str

    expected_value: float = 0.0
    probability: float = 0.0

    pipeline_id: Optional[str] = None
    stage_id: Optional[str] = None

    expected_close_date: Optional[date] = None

    status: OpportunityStatus = OpportunityStatus.OPEN

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class Pipeline:
    pipeline_id: str
    name: str

    description: Optional[str] = None

    is_default: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class PipelineStage:
    stage_id: str
    pipeline_id: str

    name: str

    order: int = 1
    probability: float = 0.0

    is_closed: bool = False


@dataclass(slots=True)
class CRMActivity:
    activity_id: str

    related_type: str
    related_id: str

    activity_type: ActivityType

    description: str

    performed_by: Optional[str] = None

    performed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class CRMTask:
    task_id: str

    related_type: str
    related_id: str

    title: str
    description: str = ""

    assigned_to: Optional[str] = None

    due_date: Optional[date] = None

    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.OPEN

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class CRMNote:
    note_id: str

    related_type: str
    related_id: str

    content: str

    created_by: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class QuoteItem:
    item_name: str

    quantity: float
    unit_price: float

    discount: float = 0.0

    @property
    def total(self) -> float:
        return (self.quantity * self.unit_price) - self.discount


@dataclass(slots=True)
class Quote:
    quote_id: str

    opportunity_id: str

    items: list[QuoteItem] = field(default_factory=list)

    status: QuoteStatus = QuoteStatus.DRAFT

    valid_until: Optional[date] = None

    @property
    def subtotal(self) -> float:
        return sum(item.total for item in self.items)

    @property
    def total(self) -> float:
        return self.subtotal


@dataclass(slots=True)
class FollowUp:
    follow_up_id: str

    related_type: str
    related_id: str

    scheduled_for: datetime

    assigned_to: Optional[str] = None

    status: FollowUpStatus = FollowUpStatus.PENDING


@dataclass(slots=True)
class CustomerJourneyEvent:
    event_id: str

    customer_id: str

    stage: str

    source: str

    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class CRMAnalyticsSnapshot:
    business_id: str

    snapshot_date: date

    total_leads: int = 0
    qualified_leads: int = 0

    open_opportunities: int = 0

    won_opportunities: int = 0
    lost_opportunities: int = 0

    pipeline_value: float = 0.0

    conversion_rate: float = 0.0
@dataclass(slots=True)
class WhatsAppActivity:
    activity_id: str
    business_id: str
    related_type: str
    related_id: str
    message_id: str
    direction: str
    phone_number: str
    message: str
    status: str
    logged_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    tenant_id: Optional[str] = None
