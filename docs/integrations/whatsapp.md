# WhatsApp Cloud API — Heshly Implementation

Use placeholders for all IDs/tokens. Heshly code: `heshly_core/api/whatsapp.py` (`WhatsAppAPI.webhook/send_message/resolve_tenant`), `services/whatsapp/` (`WebhookEventParser`, `IncomingMessageProcessor`, `ConversationFlow`, `WhatsAppCloudAPIClient`, `WhatsAppOutgoingMessageSender`), `Heshly WhatsApp Configuration` (`phone_number_id 1192499907286007` test), `Heshly WhatsApp Number` → `Business Account` → `tenant_id`.

## Meta setup

- Developer account, Business portfolio, WABA, phone number `+2547…` registration.
- Embedded Signup: `Callback URL = https://n8n.heshly.com/webhook/heshly/whatsapp/incoming` or directly `https://erp.heshly.com/api/method/heshly_core.api.whatsapp.webhook`; verification via `verify_webhook` (`hub.mode=subscribe`, `hub.verify_token`, `hub.challenge`).
- Subscriptions: `messages`, `message_status`.
- Permissions: `whatsapp_business_messaging`, `whatsapp_business_management`.

## Heshly config

- `Heshly WhatsApp Configuration` (`configuration_id`, `phone_number_id`, `verify_token`, `access_token`, `app_secret`, `tenant_id=business_id=HESHLY`, `active=1`) + `Heshly WhatsApp Number` (`phone_number_id`, `phone_number`, `active`).
- Env/template: `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_PHONE_NUMBER_ID=1192499907286007` — see `.env.example`.

## Webhook flow

`Meta → POST (X-Hub-Signature-256 optional) → n8n WF1 → Frappe webhook? Or Meta → Frappe webhook directly?` Production: `Meta → n8n WF1 webhook → Normalize Payload (code) → Resolve Tenant (POST .../whatsapp.resolve_tenant) → Find/Create Lead → Build CRM Context → ... → orchestrator → delivery`. `webhook()` normalizes `entry[0].changes[0].value {messages[0].from→phone_number, text.body→text, metadata.phone_number_id}`, checks `WhatsappDuplicateEventDetector`, emits `IncomingMessageEvent`.

`resolve_tenant(phone_number_id)→{success, tenant_id, business_id, phone_number_id}` via `Heshly WhatsApp Number (phone_number_id, active=1) → Business Account (business_id, status=Active, tenant_id match)` or fallback `Heshly WhatsApp Configuration`.

## Sending

`POST https://erp.heshly.com/api/method/heshly_core.api.whatsapp.send_message {phone_number, text|message, phone_number_id, conversation_id?}` → `WhatsAppConfigurationRepository.get_by_phone_number_id → WhatsAppManager.send_message(configuration, WhatsAppMessage)` → `WhatsAppCloudAPIClient.send_message` → `WhatsAppActivityLogger → Heshly WhatsApp Activity` (tenant `configuration.tenant_id`). `delivery 502` was upstream `vite` failure, not WhatsApp.

Verify: `curl https://erp.heshly.com/api/method/heshly_core.api.agents.dispatcher.handle -d '{"text":"My house is infested with rats"}'` → `pest_control`; `curl https://erp.heshly.com/webhook/heshly/whatsapp/incoming` is n8n, not Frappe.
