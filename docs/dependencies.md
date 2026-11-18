# Dependencies — Roles, Install, Backup

## PostgreSQL (n8n) — `postgres:16`, volume `n8n-postgres/postgres_data`, `DB=n8n`

`docker run ... postgres:16`. Backup: `docker exec n8n-postgres-db pg_dump -U n8n n8n | gzip > backup.sql.gz`.

## Redis — `redis:6.2-alpine` (`redis-cache`, `redis-queue`)

`frappe_docker` compose, `DB: redis://redis-cache:6379`. Backup: append-only volume `sites/`.

## MariaDB — `mariadb:11.8` (frappe DB)

Inside `frappe_docker-db-1`. Frappe site `erp.heshly.com` DB `_d9e389f22454c161`. Backup: `bench --site erp.heshly.com backup --with-files` → `sites/erp.heshly.com/private/backups/`.

## Docker / Compose

`29.6.1` / `v5.2.0`. `compose.yaml` mounts `heshly_core` as bind mount.

## NPM — `jc21/nginx-proxy-manager:latest`, host `3` wildcard `*.heshly.com → 172.24.0.1:5173`, host `7` `heshly.com+www → 172.24.0.1:5173`, host `1` `n8n.heshly.com → n8n:5678`, host `2` `erp.heshly.com → erp:8080`. See `docs/architecture.md`. Do not change DNS without evidence.

## OpenAI

OpenRouter `gpt-5-mini` via `Workflow 2` (prompt: Meta/WhatsApp reception, not committed as source — see `heshly_core/services/ai/`). Key via `OPENAI_API_KEY` / `OPENROUTER_API_KEY` in Frappe site config or n8n credentials (not in repo).

## Calendar

`heshly_core/services/calendar/` (`CalendarManager`, `GoogleCalendarProvider`, `ErpnextProvider`, `SchedulingEngine`), `Doctype Heshly Calendar Connection`. OAuth via `api/google_oauth.py`/`meta/oauth_callback.py`.

## Email

`heshly_core/services/reporting/email_reports.py`, Frappe email queue.

## Frontend build

Node `v24.18.1`, `npm ci` → `vite build` → `dist/` (ignored). Systemd `heshly-frontend.service` (`npm run preview -- --host 0.0.0.0 --port 5173`). See `heshly_frontend/docs/deployment.md` after frontend repo init.

All third-party as dependencies only — see `docs/installation.md` for versions.
