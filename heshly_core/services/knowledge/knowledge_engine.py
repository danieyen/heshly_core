from heshly_core.models.knowledge import KnowledgeContext

from .faq_knowledge import FAQKnowledge
from .policy_knowledge import PolicyKnowledge
from .pricing_knowledge import PricingKnowledge
from .schedule_knowledge import ScheduleKnowledge
from .service_knowledge import ServiceKnowledge
from .staff_knowledge import StaffKnowledge


class KnowledgeEngine:
    """
    Main entry point for all business knowledge.
    """

    def __init__(self, context: KnowledgeContext):
        self.context = context

        self.services = ServiceKnowledge(context)
        self.staff = StaffKnowledge(context)
        self.pricing = PricingKnowledge(context)
        self.faq = FAQKnowledge(context)
        self.policies = PolicyKnowledge(context)

        # Schedule knowledge is currently configured with default hours.
        # Later it will be loaded from ERPNext.
        self.schedule = ScheduleKnowledge()