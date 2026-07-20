#!/bin/bash

set -e

echo "=================================="
echo "Heshly Disaster Recovery"
echo "=================================="

echo "Stopping services..."
docker compose -f docker-compose.production.yml down

echo "Restoring latest backup..."

LATEST_BACKUP=$(ls -t backups/*.tar.gz | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "No backup found."
    exit 1
fi

tar -xzf "$LATEST_BACKUP"

echo "Restarting services..."
docker compose -f docker-compose.production.yml up -d

echo "Disaster recovery completed successfully."