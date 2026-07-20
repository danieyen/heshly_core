from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from statistics import mean


class AILearningMetrics:
    """
    AI Learning Metrics

    Expected record

    {
        "session_id": "...",

        "intent": "BOOK_APPOINTMENT",

        "confidence_before": 0.71,

        "confidence_after": 0.93,

        "feedback_score": 5,

        "accepted_response": True,

        "corrected_by_human": False,

        "retrained": True,

        "knowledge_update": True,

        "prompt_version": "v3",

        "model": "gpt-5.5"
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        records: list[dict],
    ) -> dict:

        total = len(records)

        confidence_gain = []
        feedback_scores = []

        accepted = 0
        corrected = 0
        retrained = 0
        knowledge_updates = 0

        intent_breakdown = Counter()
        prompt_breakdown = Counter()
        model_breakdown = Counter()

        for record in records:

            before = float(
                record.get(
                    "confidence_before",
                    0.0,
                )
            )

            after = float(
                record.get(
                    "confidence_after",
                    0.0,
                )
            )

            confidence_gain.append(
                after - before
            )

            if "feedback_score" in record:

                feedback_scores.append(
                    float(
                        record["feedback_score"]
                    )
                )

            if record.get(
                "accepted_response",
                False,
            ):
                accepted += 1

            if record.get(
                "corrected_by_human",
                False,
            ):
                corrected += 1

            if record.get(
                "retrained",
                False,
            ):
                retrained += 1

            if record.get(
                "knowledge_update",
                False,
            ):
                knowledge_updates += 1

            intent_breakdown[
                record.get(
                    "intent",
                    "UNKNOWN",
                )
            ] += 1

            prompt_breakdown[
                record.get(
                    "prompt_version",
                    "unknown",
                )
            ] += 1

            model_breakdown[
                record.get(
                    "model",
                    "unknown",
                )
            ] += 1

        acceptance_rate = (
            round(
                accepted / total * 100,
                2,
            )
            if total
            else 0.0
        )

        correction_rate = (
            round(
                corrected / total * 100,
                2,
            )
            if total
            else 0.0
        )

        retraining_rate = (
            round(
                retrained / total * 100,
                2,
            )
            if total
            else 0.0
        )

        knowledge_update_rate = (
            round(
                knowledge_updates / total * 100,
                2,
            )
            if total
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_records": total,

            "accepted_responses": accepted,

            "human_corrections": corrected,

            "retrained_records": retrained,

            "knowledge_updates": knowledge_updates,

            "acceptance_rate": acceptance_rate,

            "correction_rate": correction_rate,

            "retraining_rate": retraining_rate,

            "knowledge_update_rate": knowledge_update_rate,

            "average_confidence_improvement": round(
                mean(confidence_gain),
                3,
            ) if confidence_gain else 0.0,

            "average_feedback_score": round(
                mean(feedback_scores),
                2,
            ) if feedback_scores else 0.0,

            "intent_breakdown": dict(
                intent_breakdown
            ),

            "prompt_breakdown": dict(
                prompt_breakdown
            ),

            "model_breakdown": dict(
                model_breakdown
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def most_improved_intents(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "intent_breakdown"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def most_used_prompts(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "prompt_breakdown"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def most_used_models(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "model_breakdown"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ):

        return {

            "records": report[
                "total_records"
            ],

            "acceptance_rate": report[
                "acceptance_rate"
            ],

            "correction_rate": report[
                "correction_rate"
            ],

            "retraining_rate": report[
                "retraining_rate"
            ],

            "knowledge_update_rate": report[
                "knowledge_update_rate"
            ],

            "average_confidence_improvement": report[
                "average_confidence_improvement"
            ],

            "average_feedback_score": report[
                "average_feedback_score"
            ],

            "most_common_intent": self.most_improved_intents(
                report,
                1,
            ),

            "most_used_prompt": self.most_used_prompts(
                report,
                1,
            ),

            "most_used_model": self.most_used_models(
                report,
                1,
            ),

        }