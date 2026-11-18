# Heshly — Installation Guide (Frappe + ERPNext + Heshly Core)

This guide rebuilds the Heshly backend on a fresh Ubuntu VPS using the exact versions running in production on 2026-11-18.

## 1. Production versions (verified 2026-11-18)

- **OS:** Ubuntu 26.04 LTS (Resolute) — works on 22.04/24.04 too
- **Python:** `3.14` (bench image: `python 3.14.2`, fallback 3.11+ supported by Frappe `16.x`)
- **Node:** `v24.18.1` (`/home/dan/.nvm/versions/node/v24.18.1`) — any Node 20+ works; frontend `vite 7.x` needs Node ≥20
- **Frappe:** `16.28.0` (`frappe/__init__.py:__version__`)
- **ERPNext:** `16.29.0` (`erpnext/__init__.py:__version__`)
- **Bench:** `5.31.0` (`bench --version`)
- **MariaDB:** `10.11.18` (inside `frappe_docker-db-1`); host not required if using Docker
- **Redis:** `redis:6.2-alpine` (two services `redis-cache`, `redis-queue`)
- **Docker:** `29.6.1`, **Docker Compose** `v5.2.0`
- **n8n:** `2.28.3` (`docker.n8n.io/n8nio/n8n:latest`) — separate stack, not in frappe compose
- **Heshly Core:** `0.0.1` branch `main` (or current `main` HEAD `3bbd4f1`) from `https://github.com/danieyen/heshly_core`

## 2. Prerequisites

```bash
sudo apt update && sudo apt install -y git curl python3-dev python3-venv redis-tools mariadb-client
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER  # re-login
```

Install Node via nvm (as VPS does):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc; nvm install 24; nvm use 24
```

## 3. Frappe Docker (production stack used here)

Heshly production uses the `frappe_docker` compose, not `bench init` bare-metal. Clone the infrastructure:

```bash
git clone https://github.com/danieyen/heshly_core ~/heshly_projects/heshly_core
cd ~/frappe_docker
git clone https://github.com/frappe/frappe_docker
```

`frappe_docker/compose.yaml` (Heshly variant) mounts `~/heshly_projects/heshly_core:/home/frappe/frappe-bench/apps/heshly_core` into `backend`. Services: `backend` (`heshly-erpnext:v16`), `frontend` (`:8080`), `db` (`mariadb:11.8`), `redis-cache`/`redis-queue`, `websocket`, `queue-short`/`queue-long`, `scheduler`, `configurator`, `create-site`.

`frappe_docker/apps.json`:

```json
[
  {"url": "https://github.com/frappe/erpnext", "branch": "version-16"},
  {"url": "https://github.com/danieyen/heshly_core", "branch": "main"}
]
```

### Build or pull the image

Production uses a prebuilt `heshly-erpnext:v16` (Frappe 16.28 + ERPNext 16.29 + heshly_core). To rebuild:

```bash
docker compose -f compose.yaml build
```

## 4. Create site

With `frappe_docker` running `configurator` sets `common_site_config.json`:

```
db_host=db, db_port=3306, redis_cache=redis://redis-cache:6379,
redis_queue=redis://redis-queue:6379, redis_socketio=redis://redis-queue:6379, socketio_port=9000
```

Create site (run inside `backend` or via `create-site` service):

```bash
docker compose exec backend bench new-site erp.heshly.com \
  --mariadb-root-password admin --admin-password admin
docker compose exec backend bench --site erp.heshly.com install-app erpnext
docker compose exec backend bench --site erp.heshly.com install-app heshly_core
docker compose exec backend bench --site erp.heshly.com migrate
docker compose exec backend bench --site erp.heshly.com build --app heshly_core
docker compose exec backend bench restart
```

## 5. Frontend assets

Heshly frontend is a separate Vite+React repo (see `heshly_frontend`):

```bash
cd ~/heshly_projects/heshly_frontend
npm ci
npm run build   # outputs dist/
```

Production serves via `vite preview --host 0.0.0.0 --port 5173` under `systemd heshly-frontend.service`. NPM proxies `*.heshly.com` → `172.24.0.1:5173` and `heshly.com` → `172.24.0.1:5173`. See `docs/architecture.md` for proxy details.

## 6. Bench bare-metal alternative

If not using Docker:

```bash
pip install frappe-bench
bench init --frappe-branch version-16 frappe-bench --python python3.14
cd frappe-bench
bench get-app erpnext --branch version-16
bench get-app heshly_core https://github.com/danieyen/heshly_core --branch main
bench new-site erp.heshly.com --db-root-password admin
bench --site erp.heshly.com install-app erpnext
bench --site erp.heshly.com install-app heshly_core
bench --site erp.heshly.com migrate
bench build --app heshly_core
bench start  # or setup production with supervisor/nginx
```

## 7. Verification

```bash
bench --site erp.heshly.com list-apps  # frappe 16.28.0, erpnext 16.29.0, heshly_core 0.0.1
curl http://localhost:8080/api/method/heshly_core.api.health  # or appropriate health endpoint
curl http://localhost:5173/  # vite preview
```

Restore DB/files from `~/heshly_backup_*` + `sites/` volume backup as needed.
