"""Layer 2 — Heshly Network domain models. Additive, no core mutation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


class NetworkMode(str, Enum):
    CLIENT_RECEPTIONIST = "CLIENT_RECEPTIONIST"
    HESHLY_NETWORK = "HESHLY_NETWORK"


class NetworkStatus(str, Enum):
    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    QUALIFIED = "QUALIFIED"
    MATCHED = "MATCHED"
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    TIMED_OUT = "TIMED_OUT"
    REASSIGNED = "REASSIGNED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class QualificationState(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"


class RoutingStatus(str, Enum):
    IDLE = "idle"
    MATCHING = "matching"
    OFFERED = "offered"
    ASSIGNED = "assigned"
    FAILED = "failed"


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DispatchStatus(str, Enum):
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    TIMED_OUT = "TIMED_OUT"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class MembershipStatus(str, Enum):
    ACTIVE = "Active"
    PAUSED = "Paused"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"


@dataclass(slots=True)
class NetworkConversationTurn:
    role: str  # user | assistant | system | network
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    intent: str | None = None
    confidence: float | None = None
    action: str | None = None


@dataclass(slots=True)
class NetworkConversation:
    network_conversation_id: str
    customer_phone: str
    channel: str = "whatsapp"
    network_status: str = NetworkStatus.NEW.value
    qualification_state: str = QualificationState.PENDING.value
    customer_name: str | None = None
    requested_service: str | None = None
    location: str | None = None
    urgency: str = Urgency.MEDIUM.value
    preferred_time: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    qualification_data: dict[str, Any] = field(default_factory=dict)
    candidate_businesses: list[dict[str, Any]] = field(default_factory=list)
    assigned_tenant_id: str | None = None
    assigned_business_id: str | None = None
    assigned_at: datetime | None = None
    routing_status: str = RoutingStatus.IDLE.value
    offer_attempt: int = 0
    expires_at: datetime | None = None
    source_phone_number_id: str | None = None
    turn_count: int = 0
    last_message_at: datetime | None = None
    turns: list[NetworkConversationTurn] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass(slots=True)
class NetworkDispatch:
    dispatch_id: str
    network_conversation_id: str
    tenant_id: str
    business_id: str
    consult_task_id: str | None = None
    status: str = DispatchStatus.OFFERED.value
    attempt_index: int = 0
    ranking_score: float | None = None
    ranking_reasons: dict[str, Any] = field(default_factory=dict)
    offered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deadline_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    responded_at: datetime | None = None
    response_channel: str | None = None
    lead_fee: float | None = None
    billing_status: str = "pending"


@dataclass(slots=True)
class NetworkMembership:
    membership_id: str
    tenant_id: str
    business_id: str
    status: str = MembershipStatus.ACTIVE.value
    service_area: str | None = None
    accepts_network_leads: bool = True
    reliability_score: float = 100.0
    total_leads_offered: int = 0
    total_leads_accepted: int = 0
    total_leads_declined: int = 0
    total_leads_timed_out: int = 0
    subscription_plan: str | None = None
    lead_fee: float | None = None
    billing_status: str = "pending"
    joined_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class CandidateScore:
    tenant_id: str
    business_id: str
    score: float
    reasons: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NetworkSettings:
    enabled: bool = False
    central_phone_number: str | None = None
    central_phone_number_id: str | None = None
    central_waba_id: str | None = None
    central_configuration_id: str | None = None
    dispatch_timeout_seconds: int = 300
    max_dispatch_attempts: int = 5
    default_lead_fee: float = 0
    currency: str = "KES"
    notify_channel: str = "whatsapp"
    central_display_name: str | None = None
    fallback_message: str | None = None
