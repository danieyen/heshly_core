#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage:"
    echo "./restore.sh backups/file.tar.gz"
    exit 1
fi

echo "Restoring backup..."

tar -xzf "$1"

echo "Restore complete."