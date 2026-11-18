# Heshly — Architecture & Request Flow

## Overview

Heshly is a service network platform. Components:

- **Frappe/ERPNext** (`heshly_core` Frappe app, `16.28/16.29`) — business logic, DocTypes, APIs, `Heshly Network` (qualify → consult → match → recommend → dispatch), WhatsApp + website chat, tenant/business management, fixtures, patches.
- **React frontend** (`heshly_frontend`, Vite+React+TS) — public site `heshly.com`, chat widget, dashboards, admin.
- **n8n** (`2.28.3`, Postgres 16, Redis) — WhatsApp ingress + AI workflow orchestration (`WF1` → `Workflow 2` → `Workflow 3/4/5/6`).
- **Nginx Proxy Manager** (`jc21/nginx-proxy-manager:latest`) — TLS terminator, `Cloudflare → NPM → (vite:5173 | erp:8080 | n8n:5678 | frappe_frontend:8080)`.

Third-party runtime only (ERPNext, Frappe, n8n, Postgres, Redis, NPM, Docker) — not committed.

## Request flow

### Web: `https://heshly.com` (Vite SPA)

`Client → Cloudflare → NPM host 3 (*.heshly.com 443) → http://172.24.0.1:5173` (systemd `heshly-frontend.service` `vite preview`). Host `7` is `heshly.com + www`. Host `3` wildcard catches `*.heshly.com` (app-specific). Hosts `5` (`test.heshly.com→frappe_frontend:8080`) and others coexist. Disruption Nov 18: vite shifted to `5174`, NPM still `5173` → `502`. Fix: `systemctl restart heshly-frontend`.

### API/ERP: `https://erp.heshly.com`

`→ NPM host 2 → http://erp:8080` (`frappe_docker-frontend-1` → `backend` via `frappe_docker` network).

### n8n WhatsApp: `https://n8n.heshly.com`

`→ NPM host 1 → http://n8n:5678`. Webhook `POST /webhook/heshly/whatsapp/incoming` (WF1). WF1 → `Resolve Tenant` (Frappe `whatsapp.resolve_tenant` with `phone_number_id`) → `Find/Create Lead` → `Build CRM Context` → `Get Conversation History` / `Get Business Knowledge` → `Build AI Payload` → `Workflow 2 (AI Receptionist)` → `Workflow 3 (Action)` → `Workflow 4 (Delivery)` etc. Execution mode: n8n `EXECUTION_MODE` default, `execution_entity` Postgres.

## Data flow

- **Heshly Network**: `qualification_service.qualify_message` → `consultation_engine.upsert_task_from_message` + `next_consultation_step` + `should_search_providers` → `matching_engine` / `dispatch_service.offer_next_for_task` → `recommendation`.
- **WhatsApp**: `WhatsappApi.webhook` → `WebhookEventParser` → `IncomingMessageProcessor` → `ConversationFlow` → `WhatsappOutgoingMessageSender` → `WhatsApp Cloud API`.
- **Website chat**: `website_chat` adapter reuses same `qualification/consultation/matching` with `channel=web`, anonymous `wa_web_<session>` prefix.

## Persistence

- Frappe site `erp.heshly.com` → MariaDB ` _d9e389f22454c161` (or `sites/` volume), Redis `redis-cache/redis-queue`, `sites/` + `assets` volumes.
- n8n → Postgres `n8n` DB (`workflow_entity`, `execution_entity`, `execution_data`), volume `n8n-postgres/postgres_data`.
- NPM → `letsencrypt` + proxy hosts under `npm` container `/data`.

## Frontend

`heshly_frontend/src`: `App.tsx` hostname routing (`isHomeService/isPublicRoot` etc.), `pages/HomeService`, `Landing`, `admin/cms`, `components/cms/TiptapEditor` + `lib/autoFormat`, `components/hcn/HcnChat`, `api/content_format.py` (nh3 sanitize). Build `vite preview --host 0.0.0.0 --port 5173`.

## Deployment artifacts

`deployment/` (Heshly-owned) stays in `heshly_core`. Optional `heshly_deployment` repo would duplicate it — not needed while small.
