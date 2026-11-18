app_name = "heshly_core"
app_title = "Heshly Core"
app_publisher = "Heshly"
app_description = "AI Receptionist & Multi-Tenant SaaS Platform"
app_email = "admin@heshly.com"
app_license = "MIT"


# =====================================================
# Request Hooks
# =====================================================

before_request = [
    "heshly_core.services.tenant.request_hooks.before_request",
]

after_request = [
    "heshly_core.services.tenant.request_hooks.after_request",
]

# Heshly tenant propagation for Appointment -> Event -> Communication lifecycle
doc_events = {
    "Communication": {
        "before_insert": "heshly_core.services.tenant.communication_tenant_hook.communication_before_insert",
    },
    "Event": {
        "before_insert": "heshly_core.services.tenant.communication_tenant_hook.event_before_insert",
    },
}


permission_query_conditions = {
    "Business Account": "heshly_core.services.tenant.permission_query_conditions.business_account_query",
    "Custom Domain": "heshly_core.services.tenant.permission_query_conditions.custom_domain_query",
    "Heshly WhatsApp Number": "heshly_core.services.tenant.permission_query_conditions.heshly_whatsapp_number_query",
    "Heshly WhatsApp Configuration": "heshly_core.services.tenant.permission_query_conditions.heshly_whatsapp_configuration_query",
    "Heshly Workflow Version": "heshly_core.services.tenant.permission_query_conditions.heshly_workflow_version_query",
    "Heshly Workflow Assignment": "heshly_core.services.tenant.permission_query_conditions.heshly_workflow_assignment_query",
    "AI Conversation": "heshly_core.services.tenant.permission_query_conditions.ai_conversation_query",
    "AI Session": "heshly_core.services.tenant.permission_query_conditions.ai_session_query",
    "Heshly WhatsApp Activity": "heshly_core.services.tenant.permission_query_conditions.heshly_whatsapp_activity_query",
    "Heshly Subscription": "heshly_core.services.tenant.permission_query_conditions.heshly_subscription_query",
    "Business Knowledge Profile": "heshly_core.services.tenant.permission_query_conditions.business_knowledge_profile_query",
    "AI Configuration": "heshly_core.services.tenant.permission_query_conditions.ai_configuration_query",
    "Appointment": "heshly_core.services.tenant.permission_query_conditions.appointment_query",
    "Event": "heshly_core.services.tenant.permission_query_conditions.event_query",
    "Lead": "heshly_core.services.tenant.permission_query_conditions.lead_query",
    "Heshly Calendar Connection": "heshly_core.services.tenant.permission_query_conditions.heshly_calendar_connection_query",
    # Layer 2 — Heshly Network (tenant-scoped where applicable)
    "Heshly Network Membership": "heshly_core.services.network.permission_query_conditions.heshly_network_membership_query",
    "Heshly Network Dispatch": "heshly_core.services.network.permission_query_conditions.heshly_network_dispatch_query",
    # Heshly Network Conversation is network-owned (no tenant row filter at DB level);
    # API enforces tenant visibility via dispatches/assigned_tenant_id — allow all for System Manager,
    # otherwise API layer filters. PQC returns 1=1 for admin, 1=0 otherwise is handled in API.
    "Heshly Network Conversation": "heshly_core.services.network.permission_query_conditions.heshly_network_conversation_query",
}


has_permission = {
    "Business Account": "heshly_core.services.tenant.document_permissions.business_account_has_permission",
    "Custom Domain": "heshly_core.services.tenant.document_permissions.custom_domain_has_permission",
    "Heshly WhatsApp Number": "heshly_core.services.tenant.document_permissions.heshly_whatsapp_number_has_permission",
    "Heshly WhatsApp Configuration": "heshly_core.services.tenant.document_permissions.heshly_whatsapp_configuration_has_permission",
    "Heshly Workflow Version": "heshly_core.services.tenant.document_permissions.heshly_workflow_version_has_permission",
    "Heshly Workflow Assignment": "heshly_core.services.tenant.document_permissions.heshly_workflow_assignment_has_permission",
    "AI Conversation": "heshly_core.services.tenant.document_permissions.ai_conversation_has_permission",
    "AI Session": "heshly_core.services.tenant.document_permissions.ai_session_has_permission",
    "Heshly WhatsApp Activity": "heshly_core.services.tenant.document_permissions.heshly_whatsapp_activity_has_permission",
    "Heshly Subscription": "heshly_core.services.tenant.document_permissions.heshly_subscription_has_permission",
    "Business Knowledge Profile": "heshly_core.services.tenant.document_permissions.business_knowledge_profile_has_permission",
    "AI Configuration": "heshly_core.services.tenant.document_permissions.ai_configuration_has_permission",
    "Appointment": "heshly_core.services.tenant.document_permissions.appointment_has_permission",
    "Event": "heshly_core.services.tenant.document_permissions.event_has_permission",
    "Lead": "heshly_core.services.tenant.document_permissions.lead_has_permission",
    "Heshly Calendar Connection": "heshly_core.services.tenant.document_permissions.heshly_calendar_connection_has_permission",
    # Layer 2 — Heshly Network
    "Heshly Network Membership": "heshly_core.services.network.document_permissions.heshly_network_membership_has_permission",
    "Heshly Network Dispatch": "heshly_core.services.network.document_permissions.heshly_network_dispatch_has_permission",
    "Heshly Network Conversation": "heshly_core.services.network.document_permissions.heshly_network_conversation_has_permission",
}

# =====================================================
# SSL Certificate Monitoring
# =====================================================

scheduler_events = {
    "hourly": [
        "heshly_core.services.custom_domain.ssl_scheduler.check_all_custom_domain_ssl",
        "heshly_core.services.network.scheduler.reconcile_timeouts",
    ],
    # Finer-grained for network dispatch (5-min timeout). Keep idempotent — safe to run even if same hour.
    "cron": {
        "*/5 * * * *": [
            "heshly_core.services.network.scheduler.reconcile_timeouts",
        ],
    },
}
