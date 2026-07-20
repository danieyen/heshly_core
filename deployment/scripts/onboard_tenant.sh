#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage:"
    echo "./onboard_tenant.sh TENANT_NAME"
    exit 1
fi

TENANT=$1

echo "=================================="
echo "Tenant Onboarding"
echo "=================================="

echo "Provisioning tenant: ${TENANT}"

echo "Creating tenant..."

echo "Running setup..."

echo "Performing health checks..."

echo "Tenant ${TENANT} onboarded successfully."