# n8n — Installation & Heshly Implementation

Do not commit n8n source. This documents how to reinstall the version running on VPS (`2.28.3`) with Heshly workflows.

## Install

```bash
# PostgreSQL 16 + n8n via Docker (as on VPS, network `proxy`)
docker run -d --name n8n-postgres-db --network proxy -e POSTGRES_DB=n8n -e POSTGRES_USER=n8n -p 5432:5432 postgres:16
docker run -d --name n8n --network proxy -p 5678:5678 \
  -e DB_TYPE=postgresdb -e DB_POSTGRESDB_HOST=n8n-postgres-db -e DB_POSTGRESDB_DATABASE=n8n \
  -e WEBHOOK_URL=https://n8n.heshly.com/ -e N8N_HOST=n8n.heshly.com -e N8N_PROTOCOL=https \
  -e GENERIC_TIMEZONE=Africa/Nairobi -e TZ=Africa/Nairobi \
  -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n:2.28.3
```

Expose via NPM host `n8n.heshly.com → http://n8n:5678` (already configured, Let's Encrypt `npm-2`).

Persistent volumes: `n8n_data:/home/node/.n8n`, `n8n-postgres/postgres_data`.

Timezone, `N8N_RELEASE_TYPE=stable`, encryption key in `~/.n8n/config` (`encryptionKey`).

## Workflows (Heshly-owned exports)

Production has ~11 workflows (some `heshly-v2-*` inactive stubs, main chain active):

- `WF1 — WhatsApp Incoming / CRM Intake v1` (`9db30e75-031f-4a83-83d6-2face7441ba0`, webhook `POST /webhook/heshly/whatsapp/incoming`, **true**) — entry.
- `Workflow 2 — AI Receptionist` (`heshly-ai-receptionist-v3`, true)
- `WF3/1-4 — AI Action` (`8f3c2a91…`, `heshly-ai-action-*`, true)
- `Workflow 3 — AI Action / Booking` (`heshly-ai-action-booking-v1`), `Workflow 4 — WhatsApp Response` (`37bdbe49…`), `Workflow 5 — Conversation/AI Analytics`, `Workflow 6 — Scheduled/Background`.

Inactive `heshly-v2-*` (orchestrator/reception/intent/dispatcher/qualification/matching/…): deterministic orchestrator stubs (`heshly_core/api/agents/orchestrator.py` + `contracts.py`) not yet fully activated pending live trace verification.

Exports in repo: `heshly_core/n8n_workflows/` (`WF3_Parent.json`, `WF4_WhatsApp_Response.json`, `WF3_2.json`), `heshly_core/n8n/workflows/` (`WF1-Get-Conversation-History.json`, `heshly-ai-receptionist-v3.json`), plus DB dumps `backups/live_*.json` (ignored) and `live_active_workflows*.json`. **Do not publish `backups/` live exports with credentials** — curate before committing.

### Import/activate order

1. `WF3/*` helpers, then `Workflow 2`, `Workflow 3/4/5/6`, finally `WF1`.
2. `WF1 → Workflow 2` via `Execute Workflow — Workflow 2` node (`workflowId.value=heshly-ai-receptionist-v3`) — verify `workflowInputs` mapping (`session_id`, `message_id`, `text`, `channel`, `tenant_id` etc. from `Build AI Payload`).
3. Resolve Tenant: `POST https://erp.heshly.com/api/method/heshly_core.api.whatsapp.resolve_tenant?phone_number_id=1192499907286007` (see `heshly_core/api/whatsapp.py`).

### Dependencies & triggers

- `WF1` webhook `heshly/whatsapp/incoming` (Meta), no `Respond to Webhook` needed.
- `Workflow 2` `ExecuteWorkflowTrigger`, OpenRouter `gpt-5-mini` (2000t) for non-deterministic paths, fallback to deterministic `_deterministic_intent/_domain`.
- Inter-workflow `Execute Workflow` deps: `WF1→W2→W3→W4` chain.
- Frappe API deps: `whatsapp.resolve_tenant`, `whatsapp.webhook`, `whatsapp.send_message`, `agents.orchestrator.orchestrate_api`, `conversations.*`, `ai.get_business_knowledge`.

### Recovery

From exports: `n8n → Settings → Import from File`, set `WEBHOOK_URL`, set Postgres `DB_*`, import `POSTGRES_DB=n8n` dump, restore `~/.n8n/config` key, activate in order above, test via `curl https://n8n.heshly.com/webhook/heshly/whatsapp/incoming`.
