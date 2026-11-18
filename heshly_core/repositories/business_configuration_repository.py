from __future__ import annotations

import json

import frappe

from heshly_core.models.business_profile import BusinessProfile
from heshly_core.models.business_settings import BusinessSettings
from heshly_core.models.business_knowledge_profile import BusinessKnowledgeProfile


class BusinessConfigurationRepository:
    """Persistent business configuration repository."""

    def __init__(self):
        self._profiles: dict[str, BusinessProfile] = {}
        self._settings: dict[str, BusinessSettings] = {}
        self._knowledge: dict[str, BusinessKnowledgeProfile] = {}

    # =====================================================
    # Profile Storage
    # =====================================================

    def save_profile(
        self,
        profile: BusinessProfile,
    ) -> BusinessProfile:

        self._profiles[profile.business_id] = profile
        return profile

    def get_profile(
        self,
        business_id: str,
    ) -> BusinessProfile | None:

        return self._profiles.get(business_id)

    # =====================================================
    # Settings Storage
    # =====================================================

    def save_settings(
        self,
        settings: BusinessSettings,
    ) -> BusinessSettings:

        self._settings[settings.business_id] = settings
        return settings

    def get_settings(
        self,
        business_id: str,
    ) -> BusinessSettings | None:

        return self._settings.get(business_id)

    # =====================================================
    # Knowledge Profile Storage
    # =====================================================

    def save_knowledge(
        self,
        knowledge: BusinessKnowledgeProfile,
    ) -> BusinessKnowledgeProfile:

        doc_name = frappe.db.get_value(
            "Business Knowledge Profile",
            {"tenant_id": knowledge.tenant_id},
            "name",
        )

        values = {
            "tenant_id": knowledge.tenant_id,
            "business_name": knowledge.business_name,
            "industry": knowledge.industry,
            "description": knowledge.description,
            "services": json.dumps(knowledge.services),
            "products": json.dumps(knowledge.products),
            "faqs": json.dumps(knowledge.faqs),
            "policies": json.dumps(knowledge.policies),
        }

        if doc_name:
            record = frappe.get_doc(
                "Business Knowledge Profile",
                doc_name,
            )

            for fieldname, value in values.items():
                setattr(record, fieldname, value)

            record.save(ignore_permissions=True)

        else:
            record = frappe.get_doc(
                {
                    "doctype": "Business Knowledge Profile",
                    **values,
                }
            )

            record.insert(ignore_permissions=True)

        frappe.db.commit()

        return knowledge

    def get_knowledge(
        self,
        tenant_id: str,
    ) -> BusinessKnowledgeProfile | None:

        row = frappe.db.get_value(
            "Business Knowledge Profile",
            {"tenant_id": tenant_id},
            [
                "tenant_id",
                "business_name",
                "industry",
                "description",
                "services",
                "products",
                "faqs",
                "policies",
            ],
            as_dict=True,
        )

        if not row:
            return None

        def _list(value):
            if not value:
                return []

            if isinstance(value, list):
                return value

            try:
                result = json.loads(value)
            except (TypeError, ValueError):
                return []

            return result if isinstance(result, list) else []

        return BusinessKnowledgeProfile(
            profile_id=row.tenant_id,
            tenant_id=row.tenant_id,
            business_name=row.business_name or "",
            industry=row.industry or "",
            description=row.description or "",
            services=_list(row.services),
            products=_list(row.products),
            faqs=_list(row.faqs),
            policies=_list(row.policies),
        )

    # =====================================================
    # Configuration
    # =====================================================

    def get_configuration(
        self,
        business_id: str,
    ) -> dict:

        return {
            "profile": self.get_profile(business_id),
            "settings": self.get_settings(business_id),
            "knowledge": self.get_knowledge(business_id),
        }

    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        business_id: str,
    ):

        self._profiles.pop(business_id, None)
        self._settings.pop(business_id, None)

        frappe.db.delete(
            "Business Knowledge Profile",
            {"tenant_id": business_id},
        )

        frappe.db.commit()

        self._knowledge.pop(business_id, None)

    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self._profiles.clear()
        self._settings.clear()
        self._knowledge.clear()

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {
            "service": "business_configuration_repository",
            "status": "healthy",
            "profiles": len(self._profiles),
            "settings": len(self._settings),
            "knowledge": len(self._knowledge),
        }
