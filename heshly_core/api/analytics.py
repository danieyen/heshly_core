from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


def _tenant() -> str:
    return TenantContext().require()


@frappe.whitelist()
def get_opportunity_analytics():
    tenant_id = _tenant()

    row = frappe.db.sql(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_count,
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS won_count,
            SUM(CASE WHEN status = 'Lost' THEN 1 ELSE 0 END) AS lost_count,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Open'
                        THEN COALESCE(opportunity_amount, 0)
                        ELSE 0
                    END
                ), 0
            ) AS pipeline_value,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Open'
                        THEN
                            COALESCE(opportunity_amount, 0)
                            * COALESCE(probability, 0)
                            / 100
                        ELSE 0
                    END
                ), 0
            ) AS weighted_pipeline

        FROM `tabOpportunity`
        WHERE custom_heshly_tenant_id = %s
        """,
        (tenant_id,),
        as_dict=True,
    )[0]

    open_count = int(row.open_count or 0)
    won_count = int(row.won_count or 0)
    lost_count = int(row.lost_count or 0)

    decided = won_count + lost_count

    return {
        "total": int(row.total or 0),
        "open": open_count,
        "won": won_count,
        "lost": lost_count,
        "pipeline_value": float(row.pipeline_value or 0),
        "weighted_pipeline": float(row.weighted_pipeline or 0),
        "win_rate": float(
            (won_count / decided) * 100
            if decided
            else 0
        ),
    }


@frappe.whitelist()
def get_appointment_analytics():
    tenant_id = _tenant()

    row = frappe.db.sql(
        """
        SELECT
            COUNT(*) AS total,

            SUM(
                CASE
                    WHEN DATE(scheduled_time) = CURDATE()
                    THEN 1
                    ELSE 0
                END
            ) AS today_count,

            SUM(
                CASE
                    WHEN status = 'Completed'
                    THEN 1
                    ELSE 0
                END
            ) AS completed_count,

            SUM(
                CASE
                    WHEN status = 'Cancelled'
                    THEN 1
                    ELSE 0
                END
            ) AS cancelled_count,

            SUM(
                CASE
                    WHEN status = 'No Show'
                    THEN 1
                    ELSE 0
                END
            ) AS no_show_count,

            SUM(
                CASE
                    WHEN created_through_portal = 1
                    THEN 1
                    ELSE 0
                END
            ) AS portal_bookings

        FROM `tabAppointment`
        WHERE custom_heshly_tenant_id = %s
        """,
        (tenant_id,),
        as_dict=True,
    )[0]

    total = int(row.total or 0)
    today = int(row.today_count or 0)
    completed = int(row.completed_count or 0)
    cancelled = int(row.cancelled_count or 0)
    no_shows = int(row.no_show_count or 0)
    portal_bookings = int(row.portal_bookings or 0)

    booking_rate = (
        (portal_bookings / total) * 100
        if total
        else 0
    )

    return {
        "total": total,
        "today": today,
        "completed": completed,
        "cancelled": cancelled,
        "no_shows": no_shows,
        "booking_rate": float(booking_rate),
    }


@frappe.whitelist()
def get_lead_analytics():
    from heshly_core.services.analytics.lead_analytics import LeadAnalyticsService

    analytics = LeadAnalyticsService().get()

    return {
        "total": analytics.total,
        "new": analytics.new,
        "qualified": analytics.qualified,
        "converted": analytics.converted,
        "lost": analytics.lost,
        "conversion": analytics.conversion,
    }


@frappe.whitelist()
def get_lead_timeline(related_id: str, related_type: str = "Lead"):
    tenant_id = _tenant()

    if not related_id:
        frappe.throw("related_id is required")

    from heshly_core.services.crm.activity_manager import ActivityManager

    manager = ActivityManager()

    whatsapp = manager.whatsapp_logger.get_history(
        related_type,
        related_id,
    )

    timeline = manager.build_timeline(
        whatsapp=whatsapp,
    )

    return {
        "related_type": related_type,
        "related_id": related_id,
        "events": [
            {
                "event_type": event.event_type,
                "title": event.title,
                "description": event.description,
                "created_at": event.created_at.isoformat()
                if event.created_at
                else None,
            }
            for event in timeline
        ],
    }


@frappe.whitelist()
def get_conversation_analytics():
    tenant_id = _tenant()

    row = frappe.db.sql("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT customer_id) AS customers,
            SUM(CASE WHEN status = "active" THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN status = "closed" THEN 1 ELSE 0 END) AS closed,
            SUM(CASE WHEN UPPER(intent) = "BOOK_APPOINTMENT" THEN 1 ELSE 0 END) AS booking_intent,
            SUM(
                CASE
                    WHEN appointment_date IS NOT NULL
                    AND appointment_date != ""
                    THEN 1 ELSE 0
                END
            ) AS appointments
        FROM `tabAI Conversation`
        WHERE tenant_id = %s
    """, (tenant_id,), as_dict=True)[0]

    return {
        "total": int(row.total or 0),
        "customers": int(row.customers or 0),
        "active": int(row.active or 0),
        "closed": int(row.closed or 0),
        "booking_intent": int(row.booking_intent or 0),
        "appointments": int(row.appointments or 0),
    }


@frappe.whitelist()
def get_whatsapp_analytics():
    tenant_id = _tenant()

    row = frappe.db.sql("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN direction = "inbound" THEN 1 ELSE 0 END) AS inbound,
            SUM(CASE WHEN direction = "outbound" THEN 1 ELSE 0 END) AS outbound,
            COUNT(DISTINCT phone_number) AS customers
        FROM `tabHeshly WhatsApp Activity`
        WHERE tenant_id = %s
    """, (tenant_id,), as_dict=True)[0]

    return {
        "total": int(row.total or 0),
        "inbound": int(row.inbound or 0),
        "outbound": int(row.outbound or 0),
        "customers": int(row.customers or 0),
    }


@frappe.whitelist()
def get_conversation_intents():
    tenant_id = _tenant()

    return frappe.db.sql("""
        SELECT
            COALESCE(NULLIF(intent, ""), "UNKNOWN") AS intent,
            COUNT(*) AS count
        FROM `tabAI Conversation`
        WHERE tenant_id = %s
        GROUP BY COALESCE(NULLIF(intent, ""), "UNKNOWN")
        ORDER BY count DESC
    """, (tenant_id,), as_dict=True)


@frappe.whitelist()
def get_conversation_services():
    tenant_id = _tenant()

    return frappe.db.sql("""
        SELECT
            COALESCE(NULLIF(service, ""), "UNKNOWN") AS service,
            COUNT(*) AS count
        FROM `tabAI Conversation`
        WHERE tenant_id = %s
        GROUP BY COALESCE(NULLIF(service, ""), "UNKNOWN")
        ORDER BY count DESC
    """, (tenant_id,), as_dict=True)


@frappe.whitelist()
def get_conversation_timeline():
    tenant_id = _tenant()

    rows = frappe.db.sql("""
        SELECT
            DATE(COALESCE(started_at, creation)) AS date,
            COUNT(*) AS conversations,
            COUNT(DISTINCT customer_id) AS customers
        FROM `tabAI Conversation`
        WHERE tenant_id = %s
        GROUP BY DATE(COALESCE(started_at, creation))
        ORDER BY date ASC
    """, (tenant_id,), as_dict=True)

    return [
        {
            "date": str(row.date),
            "conversations": int(row.conversations or 0),
            "customers": int(row.customers or 0),
        }
        for row in rows
    ]

@frappe.whitelist()
def get_ai_dashboard():
    tenant_id = _tenant()

    # ---------------------------------------------------------
    # Conversation metrics
    # ---------------------------------------------------------

    conversation = frappe.db.sql(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT customer_id) AS customers,

            SUM(
                CASE
                    WHEN status = 'active'
                    THEN 1 ELSE 0
                END
            ) AS active,

            SUM(
                CASE
                    WHEN status IN ('closed', 'completed')
                    THEN 1 ELSE 0
                END
            ) AS resolved,

            SUM(
                CASE
                    WHEN status = 'handover'
                    THEN 1 ELSE 0
                END
            ) AS escalations,

            SUM(
                CASE
                    WHEN UPPER(intent) = 'BOOK_APPOINTMENT'
                    THEN 1 ELSE 0
                END
            ) AS booking_intent,

            SUM(
                CASE
                    WHEN appointment_date IS NOT NULL
                    AND appointment_date != ''
                    THEN 1 ELSE 0
                END
            ) AS appointments,

            0 AS avg_confidence

        FROM `tabAI Conversation`
        WHERE tenant_id = %s
        """,
        (tenant_id,),
        as_dict=True,
    )[0]

    total = int(conversation.total or 0)
    resolved = int(conversation.resolved or 0)
    escalations = int(conversation.escalations or 0)
    appointments = int(conversation.appointments or 0)
    booking_intent = int(conversation.booking_intent or 0)

    # ---------------------------------------------------------
    # Session metrics
    # ---------------------------------------------------------

    session = {
        "total": 0,
        "messages": 0,
        "user_messages": 0,
        "ai_messages": 0,
        "bookings": 0,
        "resolved": 0,
        "handover": 0,
        "confidence": 0,
    }

    if frappe.db.table_exists("tabAI Session"):
        session_row = frappe.db.sql(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(message_count), 0) AS messages,
                COALESCE(SUM(user_messages), 0) AS user_messages,
                COALESCE(SUM(ai_messages), 0) AS ai_messages,
                COALESCE(SUM(booking_created), 0) AS bookings,
                COALESCE(SUM(resolved), 0) AS resolved,
                COALESCE(SUM(handed_to_human), 0) AS handover,
                COALESCE(AVG(confidence_score), 0) AS confidence
            FROM `tabAI Session`
            WHERE tenant_id = %s
            """,
            (tenant_id,),
            as_dict=True,
        )[0]

        session = {
            "total": int(session_row.total or 0),
            "messages": int(session_row.messages or 0),
            "user_messages": int(session_row.user_messages or 0),
            "ai_messages": int(session_row.ai_messages or 0),
            "bookings": int(session_row.bookings or 0),
            "resolved": int(session_row.resolved or 0),
            "handover": int(session_row.handover or 0),
            "confidence": float(session_row.confidence or 0),
        }

    # ---------------------------------------------------------
    # Recent conversations
    # ---------------------------------------------------------

    recent = frappe.db.sql(
        """
        SELECT
            conversation_id,
            customer_id,
            customer_name,
            customer_phone,
            intent,
            service,
            status,
            turn_count,
            started_at,
            last_message_at,
            appointment_date,
            appointment_time
        FROM `tabAI Conversation`
        WHERE tenant_id = %s
        ORDER BY COALESCE(last_message_at, started_at, creation) DESC
        LIMIT 20
        """,
        (tenant_id,),
        as_dict=True,
    )

    conversations = []

    for row in recent:
        if row.status == "handover":
            outcome = "Escalated"
        elif row.appointment_date:
            outcome = "Booked"
        elif row.status in ("closed", "completed"):
            outcome = "Qualified"
        else:
            outcome = "Active"

        conversations.append(
            {
                "conversation_id": row.conversation_id,
                "customer_id": row.customer_id,
                "customer_name": row.customer_name or "Unknown customer",
                "customer_phone": row.customer_phone,
                "intent": row.intent or "UNKNOWN",
                "service": row.service or "—",
                "status": row.status,
                "outcome": outcome,
                "turn_count": int(row.turn_count or 0),
                "started_at": row.started_at,
                "last_message_at": row.last_message_at,
                "appointment_date": row.appointment_date,
                "appointment_time": row.appointment_time,
            }
        )

    # ---------------------------------------------------------
    # Performance
    # ---------------------------------------------------------

    resolution_rate = (
        (resolved / total) * 100
        if total
        else 0
    )

    escalation_rate = (
        (escalations / total) * 100
        if total
        else 0
    )

    booking_rate = (
        (appointments / total) * 100
        if total
        else 0
    )

    qualification_rate = (
        ((total - escalations) / total) * 100
        if total
        else 0
    )

    avg_confidence = float(
        session["confidence"]
        if session["confidence"]
        else conversation.avg_confidence or 0
    )

    # Handle either 0-1 or 0-100 confidence storage.
    if avg_confidence <= 1:
        avg_confidence *= 100

    return {
        "profile": {
            "name": "Heshly Assistant",
            "industry": "Dental",
            "personality": "Friendly & professional",
            "channel": "WhatsApp",
            "goal": "Qualify + book",
        },

        "kpis": {
            "conversations": total,
            "qualified_leads": max(total - escalations, 0),
            "appointments": appointments,
            "conversion_rate": round(booking_rate, 1),
            "escalations": escalations,
        },

        "performance": {
            "qualification_rate": round(qualification_rate, 1),
            "booking_success": round(booking_rate, 1),
            "auto_resolution": round(resolution_rate, 1),
            "avg_confidence": round(avg_confidence, 1),
            "escalation_rate": round(escalation_rate, 1),
        },

        "session": session,

        "recent_conversations": conversations,

        "counts": {
            "customers": int(conversation.customers or 0),
            "active": int(conversation.active or 0),
            "booking_intent": booking_intent,
            "appointments": appointments,
        },
    }

@frappe.whitelist()
def get_follow_up_analytics(business_id: str):
    tenant_id = _tenant()

    if not business_id:
        frappe.throw("business_id is required")

    business = frappe.db.get_value(
        "Business Account",
        business_id,
        ["business_id", "business_name", "tenant_id"],
        as_dict=True,
    )

    if not business:
        frappe.throw("Business not found")

    if business.tenant_id != tenant_id:
        frappe.throw("Business does not belong to the current tenant")

    row = frappe.db.sql(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) AS scheduled,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
            SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) AS missed,
            SUM(
                CASE
                    WHEN status IN ('pending', 'scheduled')
                    AND scheduled_for < NOW()
                    THEN 1 ELSE 0
                END
            ) AS overdue
        FROM `tabFollow Up`
        WHERE business_id = %s
        """,
        (business_id,),
        as_dict=True,
    )[0]

    total = int(row.total or 0)
    pending = int(row.pending or 0)
    scheduled = int(row.scheduled or 0)
    completed = int(row.completed or 0)
    cancelled = int(row.cancelled or 0)
    missed = int(row.missed or 0)
    overdue = int(row.overdue or 0)

    type_rows = frappe.db.sql(
        """
        SELECT
            follow_up_type AS type,
            COUNT(*) AS count
        FROM `tabFollow Up`
        WHERE business_id = %s
        GROUP BY follow_up_type
        ORDER BY count DESC
        """,
        (business_id,),
        as_dict=True,
    )

    assignee_rows = frappe.db.sql(
        """
        SELECT
            COALESCE(NULLIF(assigned_to, ''), 'Unassigned') AS assignee,
            COUNT(*) AS count
        FROM `tabFollow Up`
        WHERE business_id = %s
        GROUP BY COALESCE(NULLIF(assigned_to, ''), 'Unassigned')
        ORDER BY count DESC
        """,
        (business_id,),
        as_dict=True,
    )

    return {
        "total": total,
        "pending": pending,
        "scheduled": scheduled,
        "completed": completed,
        "cancelled": cancelled,
        "missed": missed,
        "overdue": overdue,
        "completion_rate": round(
            (completed / total) * 100,
            1,
        ) if total else 0,
        "type_breakdown": {
            item.type or "unknown": int(item.count or 0)
            for item in type_rows
        },
        "assignee_breakdown": {
            item.assignee or "Unassigned": int(item.count or 0)
            for item in assignee_rows
        },
    }

frappe.whitelist()(get_follow_up_analytics)


@frappe.whitelist()
def get_business_analytics(business_id: str):
    if not business_id:
        frappe.throw("business_id is required")

    business = frappe.db.get_value(
        "Business Account",
        business_id,
        ["business_id", "business_name", "tenant_id", "domain", "status"],
        as_dict=True,
    )

    if not business:
        frappe.throw("Business not found")

    tenant_id = business.tenant_id

    if not tenant_id:
        frappe.throw("Business has no tenant_id")

    def query(sql, values):
        return frappe.db.sql(sql, values, as_dict=True)[0]

    opportunity = query(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_count,
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS won_count,
            SUM(CASE WHEN status = 'Lost' THEN 1 ELSE 0 END) AS lost_count,
            COALESCE(SUM(
                CASE
                    WHEN status = 'Open'
                    THEN COALESCE(opportunity_amount, 0)
                    ELSE 0
                END
            ), 0) AS pipeline_value,
            COALESCE(SUM(
                CASE
                    WHEN status = 'Open'
                    THEN COALESCE(opportunity_amount, 0)
                         * COALESCE(probability, 0) / 100
                    ELSE 0
                END
            ), 0) AS weighted_pipeline
        FROM `tabOpportunity`
        WHERE custom_heshly_tenant_id = %s
        """,
        (tenant_id,),
    )

    won = int(opportunity.won_count or 0)
    lost = int(opportunity.lost_count or 0)
    decided = won + lost

    opportunities = {
        "total": int(opportunity.total or 0),
        "open": int(opportunity.open_count or 0),
        "won": won,
        "lost": lost,
        "pipeline_value": float(opportunity.pipeline_value or 0),
        "weighted_pipeline": float(opportunity.weighted_pipeline or 0),
        "win_rate": round((won / decided) * 100, 1) if decided else 0,
    }

    appointment = query(
        """
        SELECT
            COUNT(*) AS total,
            SUM(
                CASE
                    WHEN DATE(scheduled_time) = CURDATE()
                    THEN 1 ELSE 0
                END
            ) AS today_count,
            SUM(
                CASE
                    WHEN status = 'Completed'
                    THEN 1 ELSE 0
                END
            ) AS completed_count,
            SUM(
                CASE
                    WHEN status = 'Cancelled'
                    THEN 1 ELSE 0
                END
            ) AS cancelled_count,
            SUM(
                CASE
                    WHEN status = 'No Show'
                    THEN 1 ELSE 0
                END
            ) AS no_show_count,
            SUM(
                CASE
                    WHEN created_through_portal = 1
                    THEN 1 ELSE 0
                END
            ) AS portal_bookings
        FROM `tabAppointment`
        WHERE custom_heshly_tenant_id = %s
        """,
        (tenant_id,),
    )

    total_appointments = int(appointment.total or 0)
    portal_bookings = int(appointment.portal_bookings or 0)

    appointments = {
        "total": total_appointments,
        "today": int(appointment.today_count or 0),
        "completed": int(appointment.completed_count or 0),
        "cancelled": int(appointment.cancelled_count or 0),
        "no_shows": int(appointment.no_show_count or 0),
        "booking_rate": round(
            (portal_bookings / total_appointments) * 100,
            1,
        ) if total_appointments else 0,
    }

    lead = query(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Lead' THEN 1 ELSE 0 END) AS new_count,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS qualified_count,
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS converted_count,
            SUM(CASE WHEN status = 'Do Not Contact' THEN 1 ELSE 0 END) AS lost_count
        FROM `tabLead`
        WHERE custom_heshly_tenant_id = %s
        """,
        (tenant_id,),
    )

    leads_total = int(lead.total or 0)
    converted = int(lead.converted_count or 0)

    leads = {
        "total": leads_total,
        "new": int(lead.new_count or 0),
        "qualified": int(lead.qualified_count or 0),
        "converted": converted,
        "lost": int(lead.lost_count or 0),
        "conversion": round(
            (converted / leads_total) * 100,
            1,
        ) if leads_total else 0,
    }

    conversation = query(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT customer_id) AS customers,
            SUM(
                CASE
                    WHEN status = 'active'
                    THEN 1 ELSE 0
                END
            ) AS active,
            SUM(
                CASE
                    WHEN status IN ('closed', 'completed')
                    THEN 1 ELSE 0
                END
            ) AS closed,
            SUM(
                CASE
                    WHEN UPPER(intent) = 'BOOK_APPOINTMENT'
                    THEN 1 ELSE 0
                END
            ) AS booking_intent,
            SUM(
                CASE
                    WHEN appointment_date IS NOT NULL
                    AND appointment_date != ''
                    THEN 1 ELSE 0
                END
            ) AS appointments
        FROM `tabAI Conversation`
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )

    ai_total = int(conversation.total or 0)
    ai_appointments = int(conversation.appointments or 0)
    ai_closed = int(conversation.closed or 0)
    ai_active = int(conversation.active or 0)

    conversations = {
        "total": ai_total,
        "customers": int(conversation.customers or 0),
        "active": ai_active,
        "closed": ai_closed,
        "booking_intent": int(conversation.booking_intent or 0),
        "appointments": ai_appointments,
    }

    ai = {
        "profile": {
            "name": "Heshly Assistant",
            "industry": business.business_name,
            "personality": "Friendly & professional",
            "channel": "WhatsApp",
            "goal": "Qualify + book",
        },
        "kpis": {
            "conversations": ai_total,
            "qualified_leads": max(ai_total - ai_active, 0),
            "appointments": ai_appointments,
            "conversion_rate": round(
                (ai_appointments / ai_total) * 100,
                1,
            ) if ai_total else 0,
            "escalations": 0,
        },
        "performance": {
            "qualification_rate": round(
                ((ai_total - ai_active) / ai_total) * 100,
                1,
            ) if ai_total else 0,
            "booking_success": round(
                (ai_appointments / ai_total) * 100,
                1,
            ) if ai_total else 0,
            "auto_resolution": round(
                (ai_closed / ai_total) * 100,
                1,
            ) if ai_total else 0,
            "avg_confidence": 0,
            "escalation_rate": 0,
        },
    }

    follow_ups = get_follow_up_analytics(
        business.business_id
    )

    return {
        "business": {
            "business_id": business.business_id,
            "business_name": business.business_name,
            "domain": business.domain,
            "status": business.status,
            "tenant_id": tenant_id,
        },
        "opportunities": opportunities,
        "appointments": appointments,
        "leads": leads,
        "conversations": conversations,
        "follow_ups": follow_ups,
        "ai": ai,
    }


@frappe.whitelist()
def get_client_overview():
    """Outcome-oriented overview for tenant owner dashboard — reuses existing models."""
    from heshly_core.services.tenant.tenant_context import TenantContext

    biz = None
    # Same business resolution as analytics detail
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)
    bid = frappe.session.data.get("heshly_business_id")
    if not bid:
        frappe.throw("Business session not found.", frappe.PermissionError)
    biz = frappe.db.get_value("Business Account", {"business_id": bid, "status": "Active"}, ["business_id", "business_name", "tenant_id", "domain", "status"], as_dict=True)
    if not biz:
        frappe.throw("Business account not found.", frappe.DoesNotExistError)
    tenant_id = biz.tenant_id
    # Leads (total/new/qualified) — ERPNext Lead with custom_heshly_tenant_id; QUALIFIED maps to Opportunity in ERPNext
    lr = frappe.db.sql("SELECT COUNT(*) total, SUM(CASE WHEN status='Lead' THEN 1 ELSE 0 END) new_count, SUM(CASE WHEN status IN ('Opportunity','Quotation','Interested') THEN 1 ELSE 0 END) qualified, SUM(CASE WHEN status='Converted' THEN 1 ELSE 0 END) converted FROM `tabLead` WHERE custom_heshly_tenant_id=%s", (tenant_id,), as_dict=True)[0]
    leads_total = int(lr.total or 0)
    leads_new = int(lr.new_count or 0)
    leads_qualified = int(lr.qualified or 0)
    leads_converted = int(lr.converted or 0)
    # Appointments — timezone-aware (tenant/system tz) and consistent count/list
    import datetime as _dt
    import zoneinfo as _zoneinfo

    # Resolve tenant timezone (Business Account.timezone) else System Settings
    _tzname = None
    try:
        _tzname = frappe.db.get_value("Business Account", {"tenant_id": tenant_id}, "timezone")
    except Exception:
        _tzname = None
    if not _tzname:
        try:
            _tzname = frappe.db.get_single_value("System Settings", "time_zone")
        except Exception:
            _tzname = None
    _tzname = _tzname or "Africa/Nairobi"
    try:
        _tz = _zoneinfo.ZoneInfo(_tzname)
    except Exception:
        _tz = _zoneinfo.ZoneInfo("Africa/Nairobi")
        _tzname = "Africa/Nairobi"
    # Frappe Datetime fields are stored naive in site/system tz; use tz-aware now stripped to naive for comparison
    _now_aware = _dt.datetime.now(_tz)
    _now = _now_aware.replace(tzinfo=None)
    _today = _now_aware.date()
    ap = frappe.db.sql(
        "SELECT COUNT(*) total, SUM(CASE WHEN DATE(scheduled_time)=%(today)s THEN 1 ELSE 0 END) today, SUM(CASE WHEN status IN ('Open','Scheduled','Confirmed') AND scheduled_time >= %(now)s THEN 1 ELSE 0 END) upcoming FROM `tabAppointment` WHERE custom_heshly_tenant_id=%(tid)s",
        {"today": str(_today), "now": _now, "tid": tenant_id},
        as_dict=True,
    )[0]
    ap_total = int(ap.total or 0)
    ap_today = int(ap.today or 0)
    ap_upcoming = int(ap.upcoming or 0)
    # Conversations / needs attention
    cv = frappe.db.sql("SELECT COUNT(*) total, SUM(CASE WHEN status='handover' THEN 1 ELSE 0 END) handover, SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) active FROM `tabAI Conversation` WHERE tenant_id=%s", (tenant_id,), as_dict=True)[0]
    cv_total = int(cv.total or 0)
    cv_handover = int(cv.handover or 0)
    cv_active = int(cv.active or 0)
    needs_attention = cv_handover
    # recent conversations (last 5)
    recent = frappe.db.sql("SELECT conversation_id, customer_id, customer_name, customer_phone, service, status, turn_count, started_at, last_message_at FROM `tabAI Conversation` WHERE tenant_id=%s ORDER BY COALESCE(last_message_at, modified) DESC LIMIT 5", (tenant_id,), as_dict=True)
    recent_list = [{"conversation_id": r.conversation_id, "customer": r.customer_name or r.customer_phone or r.customer_id, "service": r.service or "General", "status": r.status, "turn_count": int(r.turn_count or 0), "last_message_at": str(r.last_message_at or r.started_at or "")} for r in (recent or [])]
    # recent activity: last 10 conversation turns + appointments created
    activity = []
    for r in recent_list:
        activity.append({"at": r["last_message_at"], "title": f"{r['customer']} — {r['service']}", "kind": "conversation", "status": r["status"], "conversation_id": r["conversation_id"]})
    # upcoming appointments (next 5) — use same tz-aware cutoff as count; Appointment has no service column
    upcoming_rows = frappe.db.sql(
        "SELECT name, customer_name, customer_details, scheduled_time, status FROM `tabAppointment` WHERE custom_heshly_tenant_id=%(tid)s AND status IN ('Open','Scheduled','Confirmed') AND scheduled_time >= %(now)s ORDER BY scheduled_time ASC LIMIT 5",
        {"tid": tenant_id, "now": _now},
        as_dict=True,
    )
    upcoming = [{"name": r.name, "customer": r.customer_name or "—", "service": (r.customer_details or "")[:60] or "—", "scheduled_time": str(r.scheduled_time), "status": r.status} for r in (upcoming_rows or [])]
    # needs attention detail (top 5 handover/active with no appointment)
    needs_rows = frappe.db.sql("SELECT conversation_id, customer_name, customer_phone, customer_id, service, status, appointment_date, appointment_time, turn_count FROM `tabAI Conversation` WHERE tenant_id=%s AND status IN ('handover','active') ORDER BY COALESCE(last_message_at, modified) DESC LIMIT 5", (tenant_id,), as_dict=True)
    needs = [{"conversation_id": r.conversation_id, "customer": r.customer_name or r.customer_phone or r.customer_id, "service": r.service or "General", "status": r.status, "turn_count": int(r.turn_count or 0)} for r in (needs_rows or [])]
    return {"business": {"business_id": biz.business_id, "business_name": biz.business_name, "domain": biz.domain, "status": biz.status}, "leads": {"total": leads_total, "new": leads_new, "qualified": leads_qualified, "converted": leads_converted}, "appointments": {"total": ap_total, "today": ap_today, "upcoming": ap_upcoming, "upcoming_list": upcoming}, "conversations": {"total": cv_total, "active": cv_active, "handover": cv_handover}, "needs_attention": {"count": needs_attention, "items": needs}, "recent": recent_list, "activity": activity}
