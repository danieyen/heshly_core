from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta

from heshly_core.models.calendar import AppointmentRequest
from heshly_core.models.conversation import (
    Conversation,
    ConversationTurn,
    Speaker,
)
from heshly_core.models.intent import Intent

from heshly_core.services.ai.decision_engine import DecisionEngine
from heshly_core.services.calendar.calendar_integration import (
    CalendarIntegration,
)
from heshly_core.services.calendar.providers.erpnext_provider import (
    ERPNextCalendarProvider,
)

from heshly_core.services.calendar.providers.provider_integration import (
    ProviderIntegration,
)
from heshly_core.models.calendar import (
    CalendarConfiguration,
    CalendarProvider,
)
from heshly_core.models.calendar_provider import (
    ProviderConnection,
    ProviderEventQuery,
)

from heshly_core.services.conversation.conversation_manager import (
    ConversationManager,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
)


class WhatsAppConversationOrchestrator:
    """
    Connects WhatsApp messages to the Heshly conversation,
    AI decision engine, and real calendar booking flow.
    """

    DEFAULT_DURATION_MINUTES = 30
    DEFAULT_TIMEZONE = "Africa/Nairobi"

    def __init__(self) -> None:
        self._decision_engine = DecisionEngine()
        self._calendar = CalendarIntegration()

    def _conversation_id(
        self,
        event: IncomingMessageEvent,
        tenant_id: str,
    ) -> str:
        return f"{tenant_id}:{event.phone_number}"

    def _get_or_create(
        self,
        conversation_id: str,
        event: IncomingMessageEvent,
        tenant_id: str,
    ) -> tuple[Conversation, ConversationManager]:

        manager = ConversationManager(
            tenant_id=tenant_id,
            channel="whatsapp",
        )

        conversation = manager.get(conversation_id)

        if conversation is None:
            conversation = manager.create(
                conversation_id=conversation_id,
                customer_id=event.phone_number,
            )

        return conversation, manager

    @staticmethod
    def _merge_entities(
        conversation: Conversation,
        extracted,
    ) -> None:

        if extracted.service:
            conversation.entities.service = extracted.service

        if extracted.date:
            conversation.entities.date = extracted.date

        if extracted.time:
            conversation.entities.time = extracted.time

        if extracted.customer_name:
            conversation.entities.customer_name = (
                extracted.customer_name
            )

        if extracted.phone:
            conversation.entities.phone = extracted.phone

        if extracted.email:
            conversation.entities.email = extracted.email

        if extracted.extras:
            conversation.entities.extras.update(
                extracted.extras
            )

    @staticmethod
    def _active_intent(
        conversation: Conversation,
        current_intent: Intent,
    ) -> Intent:

        if current_intent != Intent.UNKNOWN:
            return current_intent

        if (
            conversation.entities.service
            or conversation.entities.date
            or conversation.entities.time
        ):
            return Intent.BOOK_APPOINTMENT

        return current_intent

    @staticmethod
    def _parse_time(value: str) -> time | None:
        """
        Convert values such as:
            2 pm
            2pm
            10:30 am
            10:30am
        into datetime.time.
        """

        if not value:
            return None

        match = re.fullmatch(
            r"\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*",
            value.lower(),
        )

        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        meridiem = match.group(3)

        if hour < 1 or hour > 12 or minute > 59:
            return None

        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0

        return time(hour=hour, minute=minute)

    @staticmethod
    def _parse_date(value: str, today: date | None = None) -> date | None:
        """
        Convert MVP natural-language dates into a concrete date.

        Supported:
            today
            tomorrow
            monday ... sunday
            next monday ... next sunday
        """

        if not value:
            return None

        today = today or date.today()
        normalized = value.strip().lower()

        if normalized == "today":
            return today

        if normalized == "tomorrow":
            return today + timedelta(days=1)

        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        normalized = re.sub(r"^(next|on)\s+", "", normalized)
        normalized = normalized.strip()

        if normalized in weekdays:
            target = weekdays[normalized]
            days_ahead = (target - today.weekday()) % 7

            # "next Tuesday" should mean the upcoming Tuesday,
            # but if today is Tuesday, choose the following Tuesday.
            if days_ahead == 0:
                days_ahead = 7

            return today + timedelta(days=days_ahead)

        return None

    def _duration_minutes(
        self,
        tenant_id: str,
        service: str,
    ) -> int:
        """
        Resolve appointment duration from tenant configuration.

        The current Heshly configuration model has a tenant-level
        appointment_duration setting rather than a Service DocType.
        """

        try:
            from heshly_core.models.tenant_configuration import (
                TenantConfiguration,
            )

            config = TenantConfiguration(
                tenant_id=tenant_id
            )

            value = config.get(
                "appointment_duration"
            )

            if value:
                return int(value)

        except Exception:
            pass

        return self.DEFAULT_DURATION_MINUTES

    def _provider_connection(
        self,
        tenant_id: str,
    ) -> ProviderConnection:
        """
        Build the tenant's persisted calendar ProviderConnection via the
        existing repository/provider abstraction. Provider-agnostic and
        tenant-isolated. Fails clearly when no active connection exists —
        do NOT fall back to ERPNEXT.
        """
        from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
        from heshly_core.services.tenant.tenant_context import TenantContext

        # Ensure downstream provider resolution sees the correct tenant
        try:
            TenantContext().set(tenant_id)
        except Exception:
            pass

        repo = CalendarConnectionRepository()
        conns = repo.list(tenant_id=tenant_id)
        chosen = None
        if conns:
            active = [c for c in conns if str(getattr(getattr(c, "status", ""), "value", c.status)) == "active"]
            pool = active if active else conns
            chosen = pool[0] if pool else None

        if chosen is None:
            # No active calendar connection — caller must handle as fatal
            raise RuntimeError("No active calendar connection configured for this tenant")

        from heshly_core.models.calendar import CalendarConfiguration as CC
        from heshly_core.models.calendar_provider import ProviderConnection as PC

        cfg = CC(
            provider=chosen.provider,
            calendar_id=chosen.calendar_id,
            timezone=chosen.timezone or self.DEFAULT_TIMEZONE,
            tenant_id=chosen.tenant_id,
            business_name=getattr(chosen, "business_name", "") or "",
        )
        return PC(
            configuration=cfg,
            access_token=getattr(chosen, "access_token", None),
            refresh_token=getattr(chosen, "refresh_token", None),
            expires_at=getattr(chosen, "expires_at", None),
        )

    def _load_events(
        self,
        start: datetime,
        end: datetime,
        tenant_id: str,
    ):
        """
        Load existing calendar events for the tenant's persisted provider.

        Provider-agnostic: resolves ProviderConnection via
        CalendarConnectionRepository (Google/ERPNext/Outlook). No hard-coded
        provider here; tenant isolation enforced by repository.
        """

        provider = ProviderIntegration()
        provider.connect(
            self._provider_connection(tenant_id)
        )

        result = provider.get_events(
            ProviderEventQuery(
                start=start,
                end=end,
            )
        )

        if not result.success:
            raise RuntimeError(
                result.message or "Unable to load calendar events."
            )

        return result.events

    def _create_appointment(
        self,
        conversation: Conversation,
        event: IncomingMessageEvent,
        tenant_id: str,
    ):
        """
        Create appointment via the existing CalendarIntegration /
        SchedulingEngine path. No second availability engine here —
        CalendarManager/SchedulingEngine/AvailabilityEngine perform the
        authoritative availability check.
        """
        entities = conversation.entities

        appointment_date = self._parse_date(
            entities.date
        )

        appointment_time = self._parse_time(
            entities.time
        )

        if appointment_date is None:
            return {
                "success": False,
                "message": (
                    "I couldn't determine the appointment date. "
                    "Please provide a specific day."
                ),
            }

        if appointment_time is None:
            return {
                "success": False,
                "message": (
                    "I couldn't determine the appointment time. "
                    "Please provide a time such as 2 pm."
                ),
            }

        duration = self._duration_minutes(
            tenant_id,
            entities.service or "",
        )

        # Interpret the requested slot in the persisted tenant calendar timezone
        # (e.g. Europe/London for live heshly Google connection). Do not leave
        # a naive datetime; convert correctly from date+time in that tz.
        import zoneinfo

        try:
            tenant_conn = self._provider_connection(tenant_id)
            tz_name = (getattr(tenant_conn.configuration, "timezone", None) or self.DEFAULT_TIMEZONE).strip() or self.DEFAULT_TIMEZONE
        except Exception as e:
            return {"success": False, "message": str(e) or "No active calendar connection configured for this tenant", "appointment": None}
        try:
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            tz = zoneinfo.ZoneInfo(self.DEFAULT_TIMEZONE)
        try:
            naive = datetime.combine(appointment_date, appointment_time)
            start = naive.replace(tzinfo=tz)
        except Exception as e:
            return {"success": False, "message": f"Invalid appointment datetime: {e}", "appointment": None}

        end = start + timedelta(minutes=duration)

        # Fetch authoritative events for this slot window in the correct tz
        try:
            events = self._load_events(
                start=start - timedelta(minutes=1),
                end=end + timedelta(minutes=1),
                tenant_id=tenant_id,
            )
        except PermissionError as e:
            return {"success": False, "message": str(e), "appointment": None}
        except Exception as e:
            return {"success": False, "message": str(e) or "Unable to load calendar events.", "appointment": None}

        request = AppointmentRequest(
            customer_name=(
                entities.customer_name
                or event.customer_name
                or "Customer"
            ),
            customer_phone=(
                entities.phone
                or event.phone_number
            ),
            service=entities.service or "",
            start=start,
            duration_minutes=duration,
            notes=(
                f"Booked via WhatsApp. "
                f"Tenant: {tenant_id}"
            ),
        )

        # Connect CalendarIntegration to the same tenant provider
        try:
            conn_for_booking = self._provider_connection(tenant_id)
        except Exception as e:
            return {"success": False, "message": str(e), "appointment": None}
        try:
            connected = self._calendar.connect(conn_for_booking)
        except Exception as e:
            return {"success": False, "message": str(e), "appointment": None}

        if not connected:
            return {
                "success": False,
                "message": (
                    "I couldn't connect to the calendar. "
                    "Please try again."
                ),
                "appointment": None,
            }

        # Delegate to CalendarManager/SchedulingEngine — existing authoritative check
        result = self._calendar.book(
            request=request,
            events=events,
        )

        if not result.success:
            return {
                "success": False,
                "message": result.response,
                "appointment": result.appointment,
            }

        return {
            "success": True,
            "message": (
                f"You're booked for {entities.service} "
                f"on {appointment_date.strftime('%A, %d %B')} "
                f"at {appointment_time.strftime('%-I:%M %p')}."
            ),
            "appointment": result.appointment,
        }

    @staticmethod
    def _reply(
        action,
        entities,
    ) -> str:

        action_name = action.action.value

        if action_name == "ask_service":
            return (
                "Sure. What service would you like to book?"
            )

        if action_name == "ask_date":
            return (
                "What date would you like the appointment?"
            )

        if action_name == "ask_time":
            return "What time would you prefer?"

        if action_name == "escalate_human":
            return (
                "I'll connect you with a member of our "
                "team to help with that."
            )

        if action_name == "answer_question":
            return (
                "I'd be happy to help. Could you tell me "
                "a little more about what you need?"
            )

        return (
            "I'm sorry, I didn't quite understand that. "
            "Could you tell me what you need help with?"
        )

    def process(
        self,
        event: IncomingMessageEvent,
        tenant_id: str = "default",
    ) -> dict:

        if not event.text:
            return {
                "success": False,
                "message": (
                    "Only text messages are currently supported "
                    "by the AI receptionist."
                ),
            }

        conversation_id = self._conversation_id(
            event,
            tenant_id,
        )

        conversation, conversation_manager = (
            self._get_or_create(
                conversation_id,
                event,
                tenant_id,
            )
        )

        conversation_manager.add_user_message(
            conversation,
            event.text,
        )

        decision = self._decision_engine.process(
            event.text
        )

        self._merge_entities(
            conversation,
            decision.entities,
        )

        effective_intent = self._active_intent(
            conversation,
            decision.intent.intent,
        )

        accumulated_completeness = (
            self._decision_engine.completeness_checker.check(
                effective_intent,
                conversation.entities,
            )
        )

        rules = None

        if accumulated_completeness.complete:
            rules = (
                self._decision_engine.business_rules.evaluate(
                    effective_intent,
                    conversation.entities,
                )
            )

        action = (
            self._decision_engine.action_planner.plan(
                effective_intent,
                accumulated_completeness,
                rules,
            )
        )

        booking_result = None

        if (
            effective_intent == Intent.BOOK_APPOINTMENT
            and action.action.value == "create_appointment"
        ):
            booking_result = self._create_appointment(
                conversation,
                event,
                tenant_id,
            )

            reply = booking_result["message"]

            if not booking_result["success"]:
                conversation_manager.add_assistant_message(
                    conversation,
                    reply,
                )

                conversation_manager.save(
                    conversation
                )

                return {
                    "success": False,
                    "customer": {
                        "phone_number": event.phone_number,
                        "name": event.customer_name,
                    },
                    "conversation": {
                        "conversation_id": conversation_id,
                        "channel": "whatsapp",
                        "turn_count": conversation.turn_count(),
                    },
                    "request": {
                        "text": event.text,
                    },
                    "response": {
                        "reply": reply,
                        "intent": effective_intent.value,
                        "confidence": decision.intent.confidence,
                        "action": action.action.value,
                    },
                    "entities": {
                        "service": conversation.entities.service,
                        "date": conversation.entities.date,
                        "time": conversation.entities.time,
                    },
                }

        else:
            reply = self._reply(
                action,
                conversation.entities,
            )

        conversation_manager.add_assistant_message(
            conversation,
            reply,
        )

        conversation_manager.save(
            conversation
        )

        response = {
            "success": True,
            "customer": {
                "phone_number": event.phone_number,
                "name": event.customer_name,
            },
            "conversation": {
                "conversation_id": conversation_id,
                "channel": "whatsapp",
                "turn_count": conversation.turn_count(),
            },
            "request": {
                "text": event.text,
            },
            "response": {
                "reply": reply,
                "intent": effective_intent.value,
                "confidence": decision.intent.confidence,
                "action": action.action.value,
            },
            "entities": {
                "service": conversation.entities.service,
                "date": conversation.entities.date,
                "time": conversation.entities.time,
            },
        }

        if booking_result:
            appointment = booking_result.get(
                "appointment"
            )

            if appointment:
                response["appointment"] = {
                    "success": appointment.success,
                    "appointment_id": appointment.appointment_id,
                    "status": (
                        appointment.status.value
                        if appointment.status
                        else None
                    ),
                    "message": appointment.message,
                }

        return response
