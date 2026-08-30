from __future__ import annotations

import threading

from heshly_core.models.workflow_version import (
    WorkflowVersion,
)


class WorkflowVersionRepository:

    def __init__(self):

        self._versions: dict[
            str,
            list[WorkflowVersion],
        ] = {}
        self._lock = threading.RLock()

    def _validate_tenant_id(self, tenant_id: str):
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

    def save(
        self,
        version: WorkflowVersion,
    ) -> WorkflowVersion:
        if not isinstance(version, WorkflowVersion):
            raise ValueError("version must be a WorkflowVersion instance")
        self._validate_tenant_id(version.tenant_id)
        with self._lock:
            self._versions.setdefault(
                version.tenant_id,
                [],
            ).append(version)
            # Keep versions sorted by version number
            self._versions[version.tenant_id].sort(key=lambda v: v.version)
        return version

    def list(
        self,
        tenant_id: str,
    ) -> list[WorkflowVersion]:
        self._validate_tenant_id(tenant_id)
        with self._lock:
            return list(
                self._versions.get(
                    tenant_id.strip(),
                    [],
                )
            )

    def latest(
        self,
        tenant_id: str,
    ) -> WorkflowVersion | None:
        self._validate_tenant_id(tenant_id)
        with self._lock:
            versions = self._versions.get(tenant_id.strip(), [])
            if not versions:
                return None
            return max(
                versions,
                key=lambda v: v.version,
            )

    def get(
        self,
        tenant_id: str,
        version_number: int,
    ) -> WorkflowVersion | None:
        self._validate_tenant_id(tenant_id)
        if not isinstance(version_number, int) or version_number < 1:
            raise ValueError("version_number must be an integer >= 1")
        with self._lock:
            for v in self._versions.get(tenant_id.strip(), []):
                if v.version == version_number:
                    return v
        return None

    def count(
        self,
        tenant_id: str,
    ) -> int:
        self._validate_tenant_id(tenant_id)
        with self._lock:
            return len(self._versions.get(tenant_id.strip(), []))

    def clear(
        self,
        tenant_id: str | None = None,
    ) -> None:
        with self._lock:
            if tenant_id is None:
                self._versions.clear()
            else:
                self._validate_tenant_id(tenant_id)
                self._versions.pop(tenant_id.strip(), None)
