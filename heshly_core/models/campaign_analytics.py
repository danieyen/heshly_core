from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# ==========================================================
# Campaign Status
# ==========================================================

class CampaignStatus(str, Enum):

    DRAFT = "draft"

    SCHEDULED = "scheduled"

    RUNNING = "running"

    PAUSED = "paused"

    COMPLETED = "completed"

    CANCELLED = "cancelled"


# ==========================================================
# Campaign Channel
# ==========================================================

class CampaignChannel(str, Enum):

    EMAIL = "email"

    SMS = "sms"

    WHATSAPP = "whatsapp"

    FACEBOOK = "facebook"

    INSTAGRAM = "instagram"

    GOOGLE = "google"

    LINKEDIN = "linkedin"

    WEBSITE = "website"

    OTHER = "other"


# ==========================================================
# Analytics Period
# ==========================================================

class CampaignAnalyticsPeriod(str, Enum):

    DAILY = "daily"

    WEEKLY = "weekly"

    MONTHLY = "monthly"

    QUARTERLY = "quarterly"

    YEARLY = "yearly"

    CUSTOM = "custom"


# ==========================================================
# Campaign Metrics
# ==========================================================

@dataclass(slots=True)
class CampaignMetrics:

    impressions: int = 0

    reach: int = 0

    clicks: int = 0

    conversions: int = 0

    leads: int = 0

    appointments: int = 0

    customers: int = 0

    revenue: float = 0.0

    spend: float = 0.0

    ctr: float = 0.0

    conversion_rate: float = 0.0

    cpc: float = 0.0

    cpl: float = 0.0

    cpa: float = 0.0

    roi: float = 0.0

    roas: float = 0.0


# ==========================================================
# Campaign
# ==========================================================

@dataclass(slots=True)
class Campaign:

    campaign_id: str

    name: str

    channel: CampaignChannel

    status: CampaignStatus = CampaignStatus.DRAFT

    start_date: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    end_date: datetime | None = None

    budget: float = 0.0

    owner: str = ""

    metrics: CampaignMetrics = field(
        default_factory=CampaignMetrics
    )

    metadata: dict = field(
        default_factory=dict
    )


# ==========================================================
# Campaign Analytics Report
# ==========================================================

@dataclass(slots=True)
class CampaignAnalyticsReport:

    report_id: str

    business_id: str

    period: CampaignAnalyticsPeriod

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    campaigns: list[Campaign] = field(
        default_factory=list
    )

    metadata: dict = field(
        default_factory=dict
    )

    # ------------------------------------------------------

    def add_campaign(
        self,
        campaign: Campaign,
    ):

        self.campaigns.append(campaign)

    @property
    def total_campaigns(self):

        return len(self.campaigns)