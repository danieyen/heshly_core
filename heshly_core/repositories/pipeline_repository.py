from __future__ import annotations

from datetime import datetime

import frappe

from heshly_core.models.crm import (
    Pipeline,
    PipelineStage,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class PipelineRepository(BaseRepository[Pipeline]):
    """
    Persistent, tenant-aware Pipeline Repository.

    Pipelines and stages are stored in:

        Heshly Pipeline
        Heshly Pipeline Stage

    Tenant isolation is enforced through TenantContext.
    """

    PIPELINE_DOCTYPE = "Heshly Pipeline"
    STAGE_DOCTYPE = "Heshly Pipeline Stage"

    PIPELINE_ID_FIELD = "pipeline_id"
    PIPELINE_NAME_FIELD = "pipeline_name"
    STAGE_ID_FIELD = "stage_id"
    STAGE_NAME_FIELD = "stage_name"
    TENANT_FIELD = "tenant_id"

    # =====================================================
    # Pipeline CRUD
    # =====================================================

    def save(
        self,
        entity: Pipeline,
    ) -> Pipeline:

        tenant_id = self.current_tenant()

        existing_name = frappe.db.get_value(
            self.PIPELINE_DOCTYPE,
            {
                self.PIPELINE_ID_FIELD: entity.pipeline_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if existing_name:
            doc = frappe.get_doc(
                self.PIPELINE_DOCTYPE,
                existing_name,
            )
        else:
            doc = frappe.new_doc(
                self.PIPELINE_DOCTYPE
            )

        doc.pipeline_id = entity.pipeline_id
        doc.tenant_id = tenant_id
        doc.pipeline_name = entity.name
        doc.description = entity.description
        doc.is_default = 1 if entity.is_default else 0

        doc.save(
            ignore_permissions=True
        )

        frappe.db.commit()

        return self._to_pipeline(doc)

    def get(
        self,
        entity_id: str,
    ) -> Pipeline | None:

        tenant_id = self.current_tenant()

        name = frappe.db.get_value(
            self.PIPELINE_DOCTYPE,
            {
                self.PIPELINE_ID_FIELD: entity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return None

        return self._to_pipeline(
            frappe.get_doc(
                self.PIPELINE_DOCTYPE,
                name,
            )
        )

    def list(self) -> list[Pipeline]:

        tenant_id = self.current_tenant()

        rows = frappe.get_all(
            self.PIPELINE_DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_pipeline(
                frappe.get_doc(
                    self.PIPELINE_DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        tenant_id = self.current_tenant()

        pipeline_name = frappe.db.get_value(
            self.PIPELINE_DOCTYPE,
            {
                self.PIPELINE_ID_FIELD: entity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not pipeline_name:
            return False

        # -------------------------------------------------
        # Delete stages first.
        #
        # Heshly Pipeline.on_trash() intentionally prevents
        # deleting a pipeline while stages still reference it.
        # -------------------------------------------------

        stage_names = frappe.get_all(
            self.STAGE_DOCTYPE,
            filters={
                "pipeline_id": entity_id,
                self.TENANT_FIELD: tenant_id,
            },
            pluck="name",
        )

        for stage_name in stage_names:
            frappe.delete_doc(
                self.STAGE_DOCTYPE,
                stage_name,
                ignore_permissions=True,
            )

        # -------------------------------------------------
        # Delete pipeline.
        # -------------------------------------------------

        frappe.delete_doc(
            self.PIPELINE_DOCTYPE,
            pipeline_name,
            ignore_permissions=True,
        )

        frappe.db.commit()

        return True

    # =====================================================
    # Utilities
    # =====================================================

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        tenant_id = self.current_tenant()

        return bool(
            frappe.db.exists(
                self.PIPELINE_DOCTYPE,
                {
                    self.PIPELINE_ID_FIELD: entity_id,
                    self.TENANT_FIELD: tenant_id,
                },
            )
        )

    def count(self) -> int:

        tenant_id = self.current_tenant()

        return frappe.db.count(
            self.PIPELINE_DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
        )

    def clear(self) -> None:

        tenant_id = self.current_tenant()

        # Delete stages first because pipeline deletion
        # intentionally checks for remaining stages.

        stage_names = frappe.get_all(
            self.STAGE_DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            pluck="name",
        )

        for stage_name in stage_names:
            frappe.delete_doc(
                self.STAGE_DOCTYPE,
                stage_name,
                ignore_permissions=True,
            )

        pipeline_names = frappe.get_all(
            self.PIPELINE_DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            pluck="name",
        )

        for pipeline_name in pipeline_names:
            frappe.delete_doc(
                self.PIPELINE_DOCTYPE,
                pipeline_name,
                ignore_permissions=True,
            )

        frappe.db.commit()

    # =====================================================
    # Pipeline Queries
    # =====================================================

    def find_by_name(
        self,
        name: str,
    ) -> Pipeline | None:

        tenant_id = self.current_tenant()

        pipeline_name = frappe.db.get_value(
            self.PIPELINE_DOCTYPE,
            {
                self.PIPELINE_NAME_FIELD: name,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not pipeline_name:
            return None

        return self._to_pipeline(
            frappe.get_doc(
                self.PIPELINE_DOCTYPE,
                pipeline_name,
            )
        )

    def default_pipeline(
        self,
    ) -> Pipeline | None:

        tenant_id = self.current_tenant()

        pipeline_name = frappe.db.get_value(
            self.PIPELINE_DOCTYPE,
            {
                "is_default": 1,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not pipeline_name:
            return None

        return self._to_pipeline(
            frappe.get_doc(
                self.PIPELINE_DOCTYPE,
                pipeline_name,
            )
        )

    # =====================================================
    # Stage Management
    # =====================================================

    def save_stage(
        self,
        stage: PipelineStage,
    ) -> PipelineStage:

        tenant_id = self.current_tenant()

        # -------------------------------------------------
        # Verify the pipeline belongs to this tenant.
        # -------------------------------------------------

        pipeline_exists = frappe.db.exists(
            self.PIPELINE_DOCTYPE,
            {
                self.PIPELINE_ID_FIELD: stage.pipeline_id,
                self.TENANT_FIELD: tenant_id,
            },
        )

        if not pipeline_exists:
            raise frappe.ValidationError(
                f"Pipeline '{stage.pipeline_id}' was not found "
                f"for tenant '{tenant_id}'."
            )

        existing_name = frappe.db.get_value(
            self.STAGE_DOCTYPE,
            {
                self.STAGE_ID_FIELD: stage.stage_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if existing_name:
            doc = frappe.get_doc(
                self.STAGE_DOCTYPE,
                existing_name,
            )
        else:
            doc = frappe.new_doc(
                self.STAGE_DOCTYPE
            )

        doc.stage_id = stage.stage_id
        doc.tenant_id = tenant_id
        doc.pipeline_id = stage.pipeline_id
        doc.stage_name = stage.name
        doc.order = stage.order

        # Python model uses 0.0 - 1.0.
        # Frappe Percent uses 0 - 100.
        doc.probability = stage.probability * 100

        doc.is_closed = 1 if stage.is_closed else 0

        doc.save(
            ignore_permissions=True
        )

        frappe.db.commit()

        return self._to_stage(doc)

    def get_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        tenant_id = self.current_tenant()

        name = frappe.db.get_value(
            self.STAGE_DOCTYPE,
            {
                self.STAGE_ID_FIELD: stage_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return None

        return self._to_stage(
            frappe.get_doc(
                self.STAGE_DOCTYPE,
                name,
            )
        )

    def delete_stage(
        self,
        stage_id: str,
    ) -> bool:

        tenant_id = self.current_tenant()

        name = frappe.db.get_value(
            self.STAGE_DOCTYPE,
            {
                self.STAGE_ID_FIELD: stage_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return False

        frappe.delete_doc(
            self.STAGE_DOCTYPE,
            name,
            ignore_permissions=True,
        )

        frappe.db.commit()

        return True

    def list_stages(
        self,
        pipeline_id: str,
    ) -> list[PipelineStage]:

        tenant_id = self.current_tenant()

        rows = frappe.get_all(
            self.STAGE_DOCTYPE,
            filters={
                "pipeline_id": pipeline_id,
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="order asc, creation asc",
        )

        return [
            self._to_stage(
                frappe.get_doc(
                    self.STAGE_DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    def find_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        return self.get_stage(stage_id)

    def next_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        current = self.get_stage(stage_id)

        if current is None:
            return None

        stages = self.list_stages(
            current.pipeline_id
        )

        for index, stage in enumerate(stages):

            if stage.stage_id == stage_id:

                if index + 1 < len(stages):
                    return stages[index + 1]

                return None

        return None

    def previous_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        current = self.get_stage(stage_id)

        if current is None:
            return None

        stages = self.list_stages(
            current.pipeline_id
        )

        for index, stage in enumerate(stages):

            if stage.stage_id == stage_id:

                if index > 0:
                    return stages[index - 1]

                return None

        return None

    # =====================================================
    # Search
    # =====================================================

    def search(
        self,
        query: str,
    ) -> list[Pipeline]:

        query = (query or "").strip()

        if not query:
            return []

        tenant_id = self.current_tenant()

        like_query = f"%{query}%"

        rows = frappe.db.sql(
            """
            SELECT name
            FROM `tabHeshly Pipeline`
            WHERE tenant_id = %s
              AND (
                    pipeline_name LIKE %s
                    OR description LIKE %s
                  )
            ORDER BY creation DESC
            """,
            (
                tenant_id,
                like_query,
                like_query,
            ),
            as_dict=True,
        )

        return [
            self._to_pipeline(
                frappe.get_doc(
                    self.PIPELINE_DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    # =====================================================
    # Analytics
    # =====================================================

    def stage_count(
        self,
        pipeline_id: str,
    ) -> int:

        tenant_id = self.current_tenant()

        return frappe.db.count(
            self.STAGE_DOCTYPE,
            filters={
                "pipeline_id": pipeline_id,
                self.TENANT_FIELD: tenant_id,
            },
        )

    def pipeline_summary(self) -> dict:

        default = self.default_pipeline()

        tenant_id = self.current_tenant()

        return {
            "pipelines": self.count(),

            "stages": frappe.db.count(
                self.STAGE_DOCTYPE,
                filters={
                    self.TENANT_FIELD: tenant_id,
                },
            ),

            "default_pipeline": (
                default.name
                if default
                else None
            ),
        }

    # =====================================================
    # Mapping
    # =====================================================

    def _to_pipeline(
        self,
        doc,
    ) -> Pipeline:

        created_at = (
            doc.get("creation")
            or datetime.utcnow()
        )

        return Pipeline(
            pipeline_id=(
                doc.get(self.PIPELINE_ID_FIELD)
                or doc.name
            ),
            name=doc.get(self.PIPELINE_NAME_FIELD) or "",
            description=doc.get("description"),
            is_default=bool(
                doc.get("is_default")
            ),
            created_at=created_at,
        )

    def _to_stage(
        self,
        doc,
    ) -> PipelineStage:

        return PipelineStage(
            stage_id=(
                doc.get(self.STAGE_ID_FIELD)
                or doc.name
            ),
            pipeline_id=doc.get("pipeline_id"),
            name=doc.get(self.STAGE_NAME_FIELD) or "",
            order=int(
                doc.get("order") or 0
            ),
            probability=float(
                doc.get("probability") or 0
            ) / 100,
            is_closed=bool(
                doc.get("is_closed")
            ),
        )
