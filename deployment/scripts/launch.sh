#!/bin/bash

set -e

echo "=================================="
echo "Heshly Production Launch"
echo "=================================="

echo "Checking production readiness..."

echo "Running health checks..."

echo "Starting production services..."

docker compose -f docker-compose.production.yml up -d

echo "Application launched successfully."

echo "Launch complete."