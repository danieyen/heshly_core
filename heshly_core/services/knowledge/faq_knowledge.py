from typing import Optional

from heshly_core.models.knowledge import (
    FAQItem,
    KnowledgeContext,
)


class FAQKnowledge:
    """
    Provides FAQ-related business knowledge.
    """

    def __init__(self, context: KnowledgeContext):
        self.context = context

    def all(self) -> list[FAQItem]:
        return self.context.faqs

    def questions(self) -> list[str]:
        return [faq.question for faq in self.context.faqs]

    def find(self, question: str) -> Optional[FAQItem]:
        question = question.lower()

        for faq in self.context.faqs:
            if faq.question.lower() == question:
                return faq

        return None

    def answer(self, question: str) -> Optional[str]:
        faq = self.find(question)

        if faq is None:
            return None

        return faq.answer

    def exists(self, question: str) -> bool:
        return self.find(question) is not None