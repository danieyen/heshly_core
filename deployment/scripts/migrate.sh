#!/bin/bash

set -e

echo "=================================="
echo "Heshly Data Migration"
echo "=================================="

echo "Running database migrations..."

bench --site production migrate

echo "Migration completed successfully."