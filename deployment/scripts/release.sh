#!/bin/bash

set -e

VERSION=$(cat VERSION)

echo "=================================="
echo "Heshly Release Manager"
echo "=================================="

echo "Building release ${VERSION}..."

docker compose -f docker-compose.production.yml build

echo "Publishing release ${VERSION}..."

git tag "v${VERSION}"

echo "Release ${VERSION} completed."