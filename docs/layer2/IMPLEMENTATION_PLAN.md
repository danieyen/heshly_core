# Layer 2 — Heshly Network Implementation Plan

## 1. Architecture Inspection Summary

### Current ingress
- **WF1 WhatsApp Incoming**: Meta Cloud → n8n WF1 (`WF1-Get-Conversation-History.json`) → `POST /api/method/heshly_core.api.conversations.get` + `POST /api/method/heshly_core.api.whatsapp.webhook`. Meta payload `entry[0].changes[0].value.metadata.phone_number_id + messages[0]` normalized to `IncomingMessageEvent` (`services/whatsapp/webhook/webhook_models.py`). Duplicate guard in-memory (`duplicate_event_detector.py`). Signature verified via `WhatsAppAuthentication` with `Heshly WhatsApp Configuration.app_secret`.
- **Tenant resolution**: `phone_number_id` → `Heshly WhatsApp Number` (active) → `configuration_id` → `Heshly WhatsApp Configuration.tenant_id` → `TenantContext` (ContextVar, `services/tenant/tenant_context.py`). Authenticated portals resolve via `User Business Membership` → `tenant_id` in `TenantRequestMiddleware`. No default tenant (`tenant_id == ""` is error).

### WF1 → WF2 → WF3 → WF4 flow
- **WF2 AI Receptionist** (`heshly-ai-receptionist-v3.json`): `Set — Normalize AI Input` extracts `business, customer, lead, conversation, conversation_history, message, business_knowledge, tenant_id, phone_number_id, conversation_id` → `AI Agent (gpt-4o-mini, next_action ∈ CHECK_AVAILABILITY|BOOK_APPOINTMENT|UPDATE_LEAD_CUSTOMER|OTHER)` → `Code — Normalize AI Output` → `Execute Workflow — WF3 Parent`.
- **WF3 Parent** (`WF3_Parent.json`): `HTTP Request → /api/method/heshly_core.api.workflow.execute_workflow` (fallback registry) → `HTTP — Call WF3/2 Child` → `HTTP — Call WF4`.
- **WF3/2 Dental Booking Child**: `HTTP — Execute Heshly Workflow` → `POST /api/method/heshly_core.api.booking.book_appointment {tenant_id, service, date, time, customer_id}` via `services/calendar/calendar_integration.py` + `booking_engine.py`.
- **WF4 WhatsApp Response**: `HTTP — Execute WF4` → `HTTP — WhatsApp Response` → `WhatsAppOutgoingMessageSender → WhatsAppCloudAPIClient → Heshly WhatsApp Activity`.

### Data sources
- **Business Account** (`doctype/business_account`): `business_id, business_name, tenant_id (hidden), domain, email, phone, status, industry, location, timezone, currency`.
- **Heshly WhatsApp Number/Configuration**: per-tenant `phone_number ↔ phone_number_id ↔ configuration_id ↔ tenant_id ↔ app_secret/access_token`.
- **Business Knowledge Profile** (`doctype/business_knowledge_profile`): `tenant_id PK, business_name, industry, description, services/products/faqs/policies (Long Text, split by TenantAIManager)`.
- **Hours/Calendar**: `models/calendar.py:BusinessHours, TimeSlot, CalendarEvent`, `Heshly Calendar Connection {provider, active}` consumed via `TenantAIManager` + `availability_checker.py / time_slot_generator.py`.
- **Conversation/Lead/Opportunity/Booking**: `AI Conversation {conversation_id=tenant_id:phone, customer_id, status, service, appointment_date/time, customer_*, intent, turns:AI Conversation Turn}`, `models/crm.py:Lead{lead_id,business_id,status,source}`, `Opportunity{pipeline_id,stage_id}`, `Follow Up {follow_up_id,business_id,scheduled_for,status}`.

### Notifications & scheduling
- **Outbound WhatsApp**: only real sender (`outgoing_message_sender.py → cloud_api_client.py → Graph https://graph.facebook.com/{v}/{phone_number_id}/messages` + `whatsapp_activity_logger.py`). No push/email/SMS cron wired.
- **Follow Up** doc has `get_pending/process_pending` but no scheduler triggers it.
- **hooks.py:scheduler_events**: single `hourly → ssl_scheduler.check_all_custom_domain_ssl`. No Workflow-6 DocType; n8n is the de-facto scheduler (synchronous HTTP chaining). Background jobs must be added via Frappe scheduler (additive).

### Portal
- **Frontend**: Vite + React19 + TS + react-router + tanstack-query + axios (`src/api/client.ts` `baseURL=VITE_API_URL withCredentials:true`). Host-based routing in `App.tsx`: `heshly.com` public, `signup.heshly.com` signup, `*.heshly.com` → tenant portal (`RequireBusinessAuth → AppLayout → Dashboard/Appointments/Customers/Conversations/AI/Services/Analytics/Settings`). Sidebar `src/components/layout/Sidebar.tsx`. No network code exists (`grep network → 0`).

---

## 2. Design Principles (ADD → EXTEND → REUSE)

- **ADD**: new DocTypes prefixed `Heshly Network *`, new modules `heshly_core/services/network/`, new APIs `heshly_core.api.network.*`, new frontend `src/pages/client/NetworkLeads.tsx`, new n8n stub `n8n_workflows/WF_L2_Network.json`.
- **EXTEND**: `hooks.py` (`permission_query_conditions`, `has_permission`, `scheduler_events`) additively; `whatsapp.py:WhatsAppAPI.webhook()` — **do not edit core**; instead add a new `api/network_webhook.py:heshly_network_webhook` endpoint and let n8n route central-number traffic there. If Meta single webhook URL must serve both, add a **non-invasive pre-check** at top of `whatsapp.py` that delegates to network when `phone_number_id == NetworkSettings.central_phone_number_id` (early return, no mutation of tenant path).
- **REUSE**: `TenantContext`, `TenantAIManager/BusinessKnowledgeProfile`, `Business Account` queries, `WhatsAppCloudAPIClient`/activity logger, `AI Conversation` pattern (copy, not mutate), existing `ApiError` helpers, `SiteConfig` for `meta_app_id`.

No edits to WF1-WF4 nodes, prompts, or tenant isolation. Regression prevention: existing conversation/booking tests remain green; new unit tests cover network isolation only.

---

## 3. Layer 2 Data Model (additive, isolated)

### 3.1 Heshly Network Settings (Single)
`doctype/heshly_network_settings/heshly_network_settings.json`
- `enabled` (Check), `central_phone_number` (Data), `central_phone_number_id` (Data unique), `central_waba_id` (Data), `central_configuration_id` (Data), `dispatch_timeout_seconds` (Int default 300), `max_dispatch_attempts` (Int default 5), `default_lead_fee` (Currency), `currency` (Data default KES), `notify_channel` (Select: whatsapp/in_app/both default whatsapp), `updated_by/at`. Single DocType; not tenant-scoped.

### 3.2 Heshly Network Membership
`doctype/heshly_network_membership/heshly_network_membership.json`
- `membership_id` (Data PK autoname field:membership_id unique), `tenant_id` (Data reqd indexed), `business_id` (Data reqd), `status` (Select Active/Paused/Inactive/Suspended default Active), `service_area` (Data), `accepts_network_leads` (Check default 1), `reliability_score` (Float default 100), `total_leads_offered/accepted/declined/timed_out` (Int), `subscription_plan` (Data), `lead_fee` (Currency), `billing_status` (Select pending/billed/paid placeholder), `joined_at`, `updated_at`. Indexed `tenant_id+status`. Permission: `tenant_id = current_tenant`.

### 3.3 Heshly Network Conversation
`doctype/heshly_network_conversation/heshly_network_conversation.json`
- `network_conversation_id` (Data PK unique autoname field:network_conversation_id), `customer_phone` (Data reqd indexed), `customer_name` (Data), `channel` (Select whatsapp/web/other default whatsapp), `network_status` (Select NEW/QUALIFYING/QUALIFIED/MATCHED/OFFERED/ACCEPTED/DECLINED/TIMED_OUT/REASSIGNED/COMPLETED/CANCELLED default NEW indexed), `qualification_state` (Select pending/in_progress/qualified/disqualified default pending), `requested_service` (Data), `location` (Data), `urgency` (Select low/medium/high/urgent), `preferred_time` (Data), `budget_min/budget_max` (Currency), `qualification_data` (JSON Long Text), `candidate_businesses` (JSON Long Text), `assigned_tenant_id` (Data), `assigned_business_id` (Data), `assigned_at` (Datetime), `routing_status` (Select idle/matching/offered/assigned/failed default idle), `offer_attempt` (Int default 0), `expires_at` (Datetime), `source_phone_number_id` (Data), `turns` (Table Heshly Network Conversation Turn), `last_message_at`, `created_at`. Tenant field is NOT used for isolation; `assigned_tenant_id` appears only after assignment.

### 3.4 Heshly Network Conversation Turn (child Table)
`doctype/heshly_network_conversation_turn/heshly_network_conversation_turn.json`
- `istable:1`, fields `role (user/assistant/system/network)`, `message (Long Text reqd)`, `intent`, `confidence`, `action`, `timestamp (Datetime)`.

### 3.5 Heshly Network Dispatch
`doctype/heshly_network_dispatch/heshly_network_dispatch.json`
- `dispatch_id` (Data PK autoname field:dispatch_id unique), `network_conversation_id` (Data reqd indexed Link to Heshly Network Conversation), `tenant_id` (Data reqd indexed), `business_id` (Data reqd), `status` (Select OFFERED/ACCEPTED/DECLINED/TIMED_OUT/EXPIRED/CANCELLED default OFFERED indexed), `attempt_index` (Int reqd), `ranking_score` (Float), `ranking_reasons` (Small Text JSON), `offered_at` (Datetime reqd), `deadline_at` (Datetime reqd), `responded_at` (Datetime), `response_channel` (Data). Compound index `(network_conversation_id, attempt_index)`. Permission: `tenant_id = current_tenant`; admin sees all.

Future commercial fields already present: `subscription_plan, lead_fee, billing_status` on Membership (+ `lead_fee` on Dispatch if needed later).

---

## 4. Service Layer (`heshly_core/services/network/`)

| Service | Responsibility | Reuses |
|---------|---------------|--------|
| `network_mode.py` | `NetworkMode = CLIENT_RECEPTIONIST | HESHLY_NETWORK`, `detect_mode(phone_number_id) → Mode` via `Heshly Network Settings.central_phone_number_id` vs `Heshly WhatsApp Number` lookup | `Heshly Network Settings` cache |
| `network_conversation_service.py` | `get_or_create(customer_phone, customer_name, source_phone_number_id)`; `append_turn()`; `set_qualification()`; `set_status()`; `assign_to_tenant()` (atomic guard against double-assign) | Pattern copied from `conversation_manager.py`, no edit |
| `matching_engine.py` | `rank_candidates(conversation) → List[Candidate{tenant_id,business_id,score,reasons}]`. Inputs: `requested_service` vs `BusinessKnowledgeProfile.services` (substring/fuzzy), `location` vs `BusinessAccount.location/service_area`, `BusinessHours` enabled, `BusinessAccount.status==Active`, `Heshly Calendar Connection`, price overlap, `reliability_score`, `accepts_network_leads`. **No hard-coded weights** — scoring dict passed in or default `SERVICE_MATCH=40, LOCATION=20, AVAILABILITY=15, RELIABILITY=10, PRICE=10, RECENCY=5` configurable via Settings | `Business Account` repo, `TenantAIManager.knowledge()`, `calendar` services |
| `dispatch_service.py` | `offer_next(conversation_id)` (picks top unscored candidate not yet dispatched, creates `Heshly Network Dispatch` OFFERED with `deadline_at=now+timeout`, bumps `offer_attempt`, sets `network_status=OFFERED`), `accept(dispatch_id, tenant_context)`, `decline()`, `timeout_expired()` (called by scheduler), `reassign()` — enforces sequential exclusivity, prevents double-assign via `frappe.db.exists Dispatch status ACCEPTED for same conversation` guard + row lock | `WhatsAppCloudAPIClient` via notification service |
| `notification_service.py` | `notify_business(dispatch)` concise summary (service/location/urgency/preferred_time/budget/deadline + ACCEPT/DECLINE links), `notify_timeout(previous_tenant)`, `notify_customer_assigned(conversation)` seamless message (e.g. "I'm finding the best available option" → "You're connected to Business X"). Reuses `WhatsAppOutgoingMessageSender`/`ActivityLogger` but sends from business perspective where needed | `services/whatsapp/*` |
| `qualification_service.py` | Minimal orchestration: distinguishes `MODE` and reuses WF2 intelligence. For HESHLY_NETWORK, uses lightweight qualifier (extracts `requested_service/location/urgency/preferred_time/budget` via regex/keyword + optional call to existing `TenantAIManager` prompt stub). Does **not** duplicate WF2 prompt. Falls back to rule-based if AI not configured | Existing `services/ai/tenant_ai_manager.py`, `services/conversation/` |
| `scheduler.py` | `reconcile_timeouts()` — `SELECT Dispatch WHERE status=OFFERED AND deadline_at < NOW()` → mark TIMED_OUT, notify, `offer_next` to next candidate; `expire_conversations()` where `max_attempts` reached → `network_status=TIMED_OUT/CANCELLED` | Frappe scheduler hook |
| `settings_service.py` | Cached read of `Heshly Network Settings` (`frappe.get_single`, 60s cache) |

Isolation guarantee: all public service methods accept `tenant_context` or `caller_tenant_id` and enforce `dispatch.tenant_id == caller` before accept/decline; `Business A` never lists `Business B` data.

---

## 5. API Layer (additive `heshly_core/api/network/`)

- `heshly_core/api/network_webhook.py` — `heshly_network_webhook(payload, headers)` handles Heshly Central WhatsApp Meta payload (same shape as client). Verifies signature against `Heshly Network Settings.central_configuration_id → Heshly WhatsApp Configuration`. Creates/updates `Heshly Network Conversation`, appends turn, triggers `qualification_service` then `matching_engine` then `dispatch_service.offer_next`. Returns `{success, mode, network_conversation_id, network_status}`. Guest-allowed (`allow_guest=True`) like `whatsapp.py:webhook`, but sets `TenantContext` to `_network` internally for DocType writes with `ignore_permissions=True` + explicit audit.
- `heshly_core/api/network_membership.py` — `get_my_membership / join_network / pause_network / update_network_preferences` — requires `TenantContext.require()`, writes `Heshly Network Membership` scoped to caller.
- `heshly_core/api/network_conversations.py` — `list_network_conversations / get_network_conversation / qualify_network_conversation` — tenant sees only conversations where a `Dispatch` exists for its `tenant_id` (or `assigned_tenant_id==caller`). Admin (System Manager + membership check) sees all with `network_status` filter.
- `heshly_core/api/network_dispatch.py` — `list_my_dispatches / get_dispatch / accept_dispatch / decline_dispatch` — enforces `dispatch.tenant_id == TenantContext.get()` and atomic accept guard. On accept, calls `assign_to_tenant` on conversation and creates optional `Lead`/`Opportunity` in tenant's CRM (`custom_heshly_tenant_id = assigned_tenant_id`) without mutating existing booking logic.
- `heshly_core/api/network_admin.py` — `admin_list_network_pipeline(status, limit)` — System Manager only, full pipeline visibility `NEW..CANCELLED`.

All APIs reuse `_unwrap_payload/_parse_json_string` tolerant helpers (copied, not imported from mutated source if needed) and `TenantContext` pattern from `api/customers.py`.

---

## 6. Tenant Isolation & Security

- **Network conversations**: `tenant_id` storage = `heshly_network` sentinel; read access gated in API by `EXISTS Dispatch WHERE tenant_id=current_tenant AND network_conversation_id=target` OR `assigned_tenant_id==current_tenant`. `has_permission` doc hooks enforce same.
- **Dispatch**: standard `tenant_id = current_tenant` row-level via `permission_query_conditions.heshly_network_dispatch_query`.
- **Membership/Settings**: `Membership` per-tenant, `Settings` Single — System Manager write, tenant read.
- No cross-tenant `Lead`/`Opportunity` leakage: assigned lead created with `custom_heshly_tenant_id = assigned_tenant_id` and normal `lead_query` PQC applies.

---

## 7. Portal Changes (minimal, reuse existing components)

- **Client**: new route `/network` under `RequireBusinessAuth → AppLayout` in `App.tsx`; `Sidebar.tsx` adds `Network Leads` (icon `Network` from lucide) after Conversations. `src/pages/client/NetworkLeads.tsx` lists `GET network_dispatch.list_my_dispatches` (cards: summary, requested_service, location, deadline, status badge, ACCEPT/DECLINE buttons + countdown), detail drawer shows qualification JSON + customer info post-assignment. `src/api/network.ts` axios client (`withCredentials:true`, tolerant unwrapping).
- **Admin**: new `src/pages/admin/NetworkPipeline.tsx` under `AdminLayout` (`/admin/network`) table + status filter chips `NEW..CANCELLED`, drill-down shows matching scores & dispatch timeline. Reuses `src/pages/admin/AdminConversations.tsx` table pattern.
- No redesign of `Conversations/Customers/Appointments`; reuse shadcn `Card, Badge, Button, Table`.

---

## 8. Scheduling & Timeouts

- `hooks.py:scheduler_events` additively extended: `"hourly": [... existing ssl, "heshly_core.services.network.scheduler.reconcile_timeouts"]` + `"all": ["..."]` if needed (keeps 5-min precision). `reconcile_timeouts` is idempotent, row-locks dispatches (`FOR UPDATE`), respects `dispatch_timeout_seconds` from `Heshly Network Settings` (configurable, not hard-coded). Does **not** touch existing `Follow Up` or reminder workflows.
- Business notification on timeout: `notification_service.notify_timeout()` sends WhatsApp fallback message.

---

## 9. Customer Experience

- Central receptionist qualifier replies via Heshly Central number only (from `central_phone_number_id` config). Messages: `NEW → "Thanks for reaching out to Heshly — finding the best option for you…"` → `OFFERED (internal only)` → `ACCEPTED → "You're connected to {Business Name} — they'll message you shortly at {phone}"`. Never leaks `Business A didn't respond`.
- After assignment, subsequent customer messages can be bridged or handed off (future: option to create tenant `AI Conversation` mirroring network turn; for MVP, keep conversation in network scope + copy to tenant on accept).

---

## 10. Non-Goals / Deferred

- Billing/payment execution (fields present, no logic).
- Bidding/auction (explicitly excluded).
- Second AI brain (reuse WF2 prompt foundation, add thin network qualifier only).

---

## 11. Safest Extension Points (verified)

1. New DocTypes under `heshly_core/heshly_core/doctype/heshly_network_*` (no core DocType edits).
2. New services `heshly_core/services/network/*` (no imports into `whatsapp/webhook/*` core).
3. New APIs `heshly_core/api/network_*.py` (new `whitelist` endpoints, no overwrite).
4. `hooks.py` additive keys only.
5. `n8n_workflows/WF_L2_Network.json` HTTP → `heshly_network_webhook` (parallel to WF1, not replacing).
6. Frontend additive route + nav item.

---

## 12. Verification Plan

- `python -m py_compile` every new module.
- `bench --site ... migrate` dry-run (DocType JSON valid).
- Manual API smoke: `POST heshly_network_webhook` with Meta sample → `Heshly Network Conversation` + `Dispatch OFFERED` → `accept_dispatch` → `assigned_tenant_id` set → second `accept` fails (409).
- Scheduler: set `dispatch_timeout_seconds=60`, dispatch → wait → `reconcile_timeouts` creates next OFFERED.
- Frontend: `npm run build` passes; tenant sees only own dispatches, admin sees pipeline.
- Existing tests: `pytest test_whatsapp_status.py test_conversation_persistence.py` green.
