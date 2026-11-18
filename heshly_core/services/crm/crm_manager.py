from __future__ import annotations

from heshly_core.repositories.repository_factory import (
    repository_factory,
)

from heshly_core.services.crm.lead_manager import (
    LeadManager,
)

from heshly_core.services.crm.opportunity_manager import (
    OpportunityManager,
)

from heshly_core.services.crm.pipeline_manager import (
    PipelineManager,
)

from heshly_core.services.crm.activity_manager import (
    ActivityManager,
)

from heshly_core.services.crm.follow_up_manager import (
    FollowUpManager,
)

from heshly_core.services.crm.quote_generator import (
    QuoteGenerator,
)

from heshly_core.services.crm.quote_items import (
    QuoteItems,
)

from heshly_core.services.crm.pricing_rules import (
    PricingRules,
)

from heshly_core.services.crm.discount_rules import (
    DiscountRules,
)

from heshly_core.services.crm.quote_approval import (
    QuoteApproval,
)

from heshly_core.services.crm.quote_status_tracker import (
    QuoteStatusTracker,
)

from heshly_core.services.crm.crm_conversation_flow import (
    CRMConversationFlow,
)


class CRMManager:
    """
    Central CRM service.

    This is the single entry point for every CRM
    capability inside Heshly.

    Modules:

        • Lead Management
        • Opportunity Management
        • Pipeline Management
        • Activity Management
        • Follow-up Engine
        • Quote Management
        • CRM Conversation Flow

    Future additions:

        • ERPNext synchronization
        • Customer Manager
        • Sales Orders
        • Invoices
        • Payments
    """

    def __init__(self):

        # Repository Layer

        self.repositories = repository_factory

        # CRM Managers

        self.leads = LeadManager()

        self.opportunities = OpportunityManager(
            repository=self.repositories.opportunities
        )

        self.pipelines = PipelineManager()

        self.activities = ActivityManager()

        self.follow_ups = FollowUpManager()

        # Quote Services

        self.quote_generator = QuoteGenerator()

        self.quote_items = QuoteItems()

        self.pricing = PricingRules()

        self.discounts = DiscountRules()

        self.quote_approval = QuoteApproval()

        self.quote_tracker = QuoteStatusTracker()

        # Conversation

        self.conversations = CRMConversationFlow()

    # =====================================================
    # Repository Access
    # =====================================================

    def repository_summary(self):

        return self.repositories.summary()

    def clear(self):

        self.repositories.clear()

    # =====================================================
    # System Health
    # =====================================================

    def health(self):

        return {

            "lead_manager": self.leads is not None,

            "opportunity_manager": (
                self.opportunities is not None
            ),

            "pipeline_manager": (
                self.pipelines is not None
            ),

            "activity_manager": (
                self.activities is not None
            ),

            "follow_up_manager": (
                self.follow_ups is not None
            ),

            "quote_generator": (
                self.quote_generator is not None
            ),

            "quote_items": (
                self.quote_items is not None
            ),

            "pricing_rules": (
                self.pricing is not None
            ),

            "discount_rules": (
                self.discounts is not None
            ),

            "quote_approval": (
                self.quote_approval is not None
            ),

            "quote_tracker": (
                self.quote_tracker is not None
            ),

            "crm_conversation_flow": (
                self.conversations is not None
            ),

        }

    # =====================================================
    # Summary
    # =====================================================

    def summary(self):

        return {

            "repositories": self.repository_summary(),

            "active_conversations": (
                self.conversations.active_sessions()
            ),

            "components": len(self.health()),

        }