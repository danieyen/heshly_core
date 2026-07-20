from __future__ import annotations

from heshly_core.models.workflow_version import (
    WorkflowVersion,
)


class WorkflowVersionRepository:

    def __init__(self):

        self._versions: dict[
            str,
            list[WorkflowVersion],
        ] = {}

    def save(
        self,
        version: WorkflowVersion,
    ) -> WorkflowVersion:

        self._versions.setdefault(
            version.tenant_id,
            [],
        ).append(version)

        return version

    def list(
        self,
        tenant_id: str,
    ) -> list[WorkflowVersion]:

        return list(
            self._versions.get(
                tenant_id,
                [],
            )
        )

    def latest(
        self,
        tenant_id: str,
    ) -> WorkflowVersion | None:

        versions = self.list(
            tenant_id
        )

        if not versions:

            return None

        return max(
            versions,
            key=lambda v: v.version,
        )