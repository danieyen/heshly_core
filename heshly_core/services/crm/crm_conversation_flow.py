from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


# ==========================================================
# CRM Conversation States
# ==========================================================

class CRMConversationState(str, Enum):

    NEW_LEAD = "new_lead"

    QUALIFICATION = "qualification"

    APPOINTMENT_BOOKING = "appointment_booking"

    OPPORTUNITY = "opportunity"

    QUOTATION = "quotation"

    NEGOTIATION = "negotiation"

    FOLLOW_UP = "follow_up"

    WON = "won"

    LOST = "lost"

    CLOSED = "closed"


# ==========================================================
# CRM Conversation Context
# ==========================================================

@dataclass(slots=True)
class CRMConversationContext:

    conversation_id: str

    customer_id: str | None = None

    lead_id: str | None = None

    opportunity_id: str | None = None

    quote_id: str | None = None

    appointment_id: str | None = None

    business_id: str | None = None

    state: CRMConversationState = (
        CRMConversationState.NEW_LEAD
    )

    variables: dict[str, Any] = field(
        default_factory=dict
    )

    history: list[dict] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# CRM Conversation Flow
# ==========================================================

class CRMConversationFlow:
    """
    Controls the CRM customer journey.

    WhatsApp
          ↓
      New Lead
          ↓
    Qualification
          ↓
    Appointment
          ↓
     Opportunity
          ↓
        Quote
          ↓
     Negotiation
          ↓
      Won / Lost
          ↓
       Follow-up
    """

    def __init__(self):

        self._sessions: dict[
            str,
            CRMConversationContext
        ] = {}

    # =====================================================
    # Session
    # =====================================================

    def create_session(
        self,
        conversation_id: str,
        business_id: str,
    ) -> CRMConversationContext:

        session = CRMConversationContext(

            conversation_id=conversation_id,

            business_id=business_id,

        )

        self._sessions[
            conversation_id
        ] = session

        return session

    def get_session(
        self,
        conversation_id: str,
    ) -> CRMConversationContext | None:

        return self._sessions.get(
            conversation_id
        )

    # =====================================================
    # State Management
    # =====================================================

    def transition(
        self,
        session: CRMConversationContext,
        state: CRMConversationState,
        reason: str = "",
    ) -> CRMConversationContext:

        previous = session.state

        session.state = state

        session.updated_at = datetime.now(
            UTC
        )

        session.history.append(

            {

                "timestamp": datetime.now(
                    UTC
                ),

                "from": previous.value,

                "to": state.value,

                "reason": reason,

            }

        )

        return session

    # =====================================================
    # Context Variables
    # =====================================================

    def set(
        self,
        session: CRMConversationContext,
        key: str,
        value: Any,
    ) -> None:

        session.variables[key] = value

    def get(
        self,
        session: CRMConversationContext,
        key: str,
        default=None,
    ):

        return session.variables.get(
            key,
            default,
        )

    # =====================================================
    # Linking CRM Records
    # =====================================================

    def attach_lead(
        self,
        session: CRMConversationContext,
        lead_id: str,
    ):

        session.lead_id = lead_id

    def attach_customer(
        self,
        session: CRMConversationContext,
        customer_id: str,
    ):

        session.customer_id = customer_id

    def attach_opportunity(
        self,
        session: CRMConversationContext,
        opportunity_id: str,
    ):

        session.opportunity_id = (
            opportunity_id
        )

    def attach_quote(
        self,
        session: CRMConversationContext,
        quote_id: str,
    ):

        session.quote_id = quote_id

    def attach_appointment(
        self,
        session: CRMConversationContext,
        appointment_id: str,
    ):

        session.appointment_id = (
            appointment_id
        )

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        session: CRMConversationContext,
    ) -> dict:

        return {

            "conversation_id": session.conversation_id,

            "business_id": session.business_id,

            "state": session.state.value,

            "lead_id": session.lead_id,

            "customer_id": session.customer_id,

            "appointment_id": session.appointment_id,

            "opportunity_id": session.opportunity_id,

            "quote_id": session.quote_id,

            "variables": len(
                session.variables
            ),

            "transitions": len(
                session.history
            ),

        }

    # =====================================================
    # Cleanup
    # =====================================================

    def close(
        self,
        conversation_id: str,
    ) -> bool:

        if conversation_id not in self._sessions:

            return False

        del self._sessions[
            conversation_id
        ]

        return True

    def active_sessions(self) -> int:

        return len(self._sessions)