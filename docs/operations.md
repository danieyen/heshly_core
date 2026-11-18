# Operations — Deployment, Backup, Restore

## Frontend deploy

```bash
cd ~/heshly_projects/heshly_frontend
npm ci && npm run build
sudo systemctl restart heshly-frontend  # vite preview :5173, check `ss -tlnp | grep 5173`, `curl http://127.0.0.1:5173/`
# NPM proxies 5173 — if port shifted to 5174, fix is restart, not NPM change (see Nov 18 incident)
curl -I https://heshly.com  # expect 200, not 502
```

## Frappe deploy

```bash
cd ~/frappe_docker
docker compose exec backend bench --site erp.heshly.com migrate
docker compose exec backend bench --site erp.heshly.com build --app heshly_core
docker compose exec backend bench restart
# Or: cp updated heshly_core into /home/frappe/frappe-bench/apps/heshly_core, py_compile
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

## Backup (preservation-first, as used 2026-11-18)

```bash
BACKUP_ROOT=~/heshly_backup_$(date +%Y%m%d_%H%M%S)
rsync -a --exclude='.git/logs' ~/heshly_projects/heshly_core/ $BACKUP_ROOT/heshly_core_filesystem/
rsync -a ~/heshly_projects/heshly_frontend/ $BACKUP_ROOT/heshly_frontend_filesystem/ --exclude node_modules  # optional
git -C ~/heshly_projects/heshly_core bundle create $BACKUP_ROOT/heshly_core.bundle --all
sha256sum $BACKUP_ROOT/*.bundle
docker exec frappe_docker-db-1 mariadb-dump ... | gzip > backup.sql.gz
```

## Restore

Clone `heshly_core` + `heshly_frontend` from GitHub, reinstall per `docs/installation.md`, restore `sites/` volume + DB dump, `vite preview` + NPM.

## SSL

`deployment/ssl/` now ignored (local `fullchain.pem`/`privkey.pem` untracked, placeholder removed). Renew via `npm` or `certbot`, keep local files, do not commit.
