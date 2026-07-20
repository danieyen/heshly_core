from __future__ import annotations

from typing import Any

from heshly_core.services.crm.crm_manager import CRMManager


class CRMIntegration:
    """
    Heshly CRM Integration Layer.

    This service acts as the bridge between the CRM module
    and the rest of Heshly.

    Current integrations:

        • AI Receptionist
        • Conversation Manager
        • Calendar Manager
        • Knowledge Manager
        • Business Manager

    Future integrations:

        • ERPNext DocTypes
        • WhatsApp Cloud API
        • Email Provider
        • SMS Provider
        • Payment Gateway
        • Reporting Engine
    """

    def __init__(self):

        self.crm = CRMManager()

    # =====================================================
    # Lead Integration
    # =====================================================

    def create_lead(self, **kwargs):

        return self.crm.leads.create(**kwargs)

    # =====================================================
    # Opportunity Integration
    # =====================================================

    def create_opportunity(self, **kwargs):

        return self.crm.opportunities.create(**kwargs)

    # =====================================================
    # Quote Integration
    # =====================================================

    def create_quote(self, **kwargs):

        return self.crm.quote_generator.create(**kwargs)

    # =====================================================
    # Conversation Integration
    # =====================================================

    def start_conversation(
        self,
        conversation_id: str,
        business_id: str,
    ):

        return self.crm.conversations.create_session(

            conversation_id=conversation_id,

            business_id=business_id,

        )

    # =====================================================
    # Repository
    # =====================================================

    def repository_summary(self):

        return self.crm.repository_summary()

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "crm": True,

            "repositories": self.crm.repository_summary(),

            "components": self.crm.health(),

        }

    # =====================================================
    # Module Summary
    # =====================================================

    def summary(self):

        return {

            "crm": self.crm.summary(),

            "repository": self.crm.repository_summary(),

        }

    # =====================================================
    # Generic Dispatch
    # =====================================================

    def execute(
        self,
        module: str,
        action: str,
        **kwargs: Any,
    ):

        module = module.lower()

        if module == "lead":

            target = self.crm.leads

        elif module == "opportunity":

            target = self.crm.opportunities

        elif module == "pipeline":

            target = self.crm.pipelines

        elif module == "activity":

            target = self.crm.activities

        elif module == "follow_up":

            target = self.crm.follow_ups

        elif module == "quote":

            target = self.crm.quote_generator

        elif module == "conversation":

            target = self.crm.conversations

        else:

            raise ValueError(

                f"Unknown CRM module: {module}"

            )

        if not hasattr(target, action):

            raise AttributeError(

                f"{target.__class__.__name__} has no action '{action}'."

            )

        method = getattr(target, action)

        return method(**kwargs)