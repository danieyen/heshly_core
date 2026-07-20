from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class HandoverStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HandoverPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EMERGENCY = "emergency"


class HandoverReason(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    LOW_CONFIDENCE = "low_confidence"
    GUARDRAIL = "guardrail"
    BUSINESS_POLICY = "business_policy"
    COMPLEX_REQUEST = "complex_request"
    EMERGENCY = "emergency"
    MANUAL = "manual"
    OTHER = "other"


@dataclass(slots=True)
class ConversationSummary:
    customer_name: str | None = None
    customer_phone: str | None = None
    requested_service: str | None = None
    qualification_status: str | None = None
    urgency: str | None = None
    booking_recommendation: str | None = None
    escalation_reason: str | None = None
    summary: str = ""


@dataclass(slots=True)
class EscalationTriggers:
    customer_requested_human: bool = False
    guardrail_escalation: bool = False
    emergency: bool = False
    low_ai_confidence: bool = False
    qualification_failed: bool = False
    booking_failed: bool = False
    conversation_stalled: bool = False


@dataclass(slots=True)
class HumanQueue:
    name: str
    priority: HandoverPriority
    department: str
    available_agents: int = 0


@dataclass(slots=True)
class ContextTransfer:
    conversation_id: str
    customer_id: str
    summary: ConversationSummary
    messages: list[str] = field(default_factory=list)
    customer_memory: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class HandoverNotification:
    recipient: str
    title: str
    message: str
    priority: HandoverPriority
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class HandoverRequest:
    customer_id: str
    conversation_id: str
    status: HandoverStatus = HandoverStatus.PENDING
    priority: HandoverPriority = HandoverPriority.NORMAL
    reason: HandoverReason = HandoverReason.OTHER
    assigned_to: str | None = None
    queue: HumanQueue | None = None
    summary: ConversationSummary | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class HumanTakeover:
    conversation_id: str
    customer_id: str
    agent_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    ai_active: bool = False