#!/bin/bash

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p ${BACKUP_DIR}

echo "Creating backup..."

tar -czf ${BACKUP_DIR}/heshly_${TIMESTAMP}.tar.gz \
    heshly_core \
    Dockerfile.production \
    docker-compose.production.yml

echo "Backup created:"
echo "${BACKUP_DIR}/heshly_${TIMESTAMP}.tar.gz"