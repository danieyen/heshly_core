#!/bin/bash

set -e

echo "=================================="
echo "Heshly Rollback"
echo "=================================="

echo "Stopping current containers..."
docker compose -f docker-compose.production.yml down

echo "Restoring previous deployment..."
docker compose -f docker-compose.production.yml up -d

echo "Rollback completed successfully."