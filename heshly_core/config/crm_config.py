from dataclasses import dataclass, field


@dataclass(slots=True)
class CRMConfig:
    """Configuration for the CRM & Pipeline module."""

    # ======================================================
    # Lead Management
    # ======================================================

    auto_create_leads: bool = True
    auto_assign_leads: bool = True
    auto_score_leads: bool = True
    require_unique_phone: bool = True
    require_unique_email: bool = False

    # ======================================================
    # Opportunity Management
    # ======================================================

    auto_create_opportunities: bool = True
    default_probability: float = 0.10

    # ======================================================
    # Pipeline
    # ======================================================

    default_pipeline: str = "Sales Pipeline"

    default_stages: list[str] = field(
        default_factory=lambda: [
            "New Lead",
            "Qualified",
            "Consultation",
            "Proposal",
            "Negotiation",
            "Won",
        ]
    )

    lost_stage: str = "Lost"

    # ======================================================
    # Follow-up
    # ======================================================

    auto_schedule_followups: bool = True

    first_followup_hours: int = 24
    second_followup_days: int = 3
    final_followup_days: int = 7

    # ======================================================
    # AI Integration
    # ======================================================

    ai_auto_qualify: bool = True
    ai_auto_update_pipeline: bool = True
    ai_generate_notes: bool = True

    # ======================================================
    # Analytics
    # ======================================================

    enable_pipeline_metrics: bool = True
    enable_conversion_metrics: bool = True
    enable_revenue_forecasting: bool = True


crm_config = CRMConfig()