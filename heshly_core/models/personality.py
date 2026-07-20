from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PersonalityTone(str, Enum):
    """
    Overall communication tone.
    """

    FRIENDLY = "friendly"

    PROFESSIONAL = "professional"

    FORMAL = "formal"

    CASUAL = "casual"

    EMPATHETIC = "empathetic"

    LUXURY = "luxury"


class ConversationStyle(str, Enum):
    """
    Response style.
    """

    SHORT = "short"

    BALANCED = "balanced"

    DETAILED = "detailed"


class GreetingStyle(str, Enum):
    """
    Greeting behaviour.
    """

    NONE = "none"

    SIMPLE = "simple"

    WARM = "warm"

    ENTHUSIASTIC = "enthusiastic"


class ClosingStyle(str, Enum):
    """
    Conversation closing behaviour.
    """

    NONE = "none"

    SIMPLE = "simple"

    FRIENDLY = "friendly"

    PROFESSIONAL = "professional"


@dataclass(slots=True)
class BrandVoice:
    """
    Business communication preferences.
    """

    business_name: str

    industry: str

    preferred_terms: list[str] = field(
        default_factory=list
    )

    forbidden_terms: list[str] = field(
        default_factory=list
    )

    allow_emojis: bool = False

    use_markdown: bool = False


@dataclass(slots=True)
class LanguageProfile:
    """
    Language preferences for the receptionist.
    """

    language_code: str = "en"

    language_name: str = "English"

    locale: str = "en-US"

    rtl: bool = False


@dataclass(slots=True)
class PersonalityProfile:
    """
    Complete receptionist personality.
    """

    name: str

    tone: PersonalityTone

    conversation_style: ConversationStyle

    greeting_style: GreetingStyle

    closing_style: ClosingStyle

    brand_voice: BrandVoice

    language: LanguageProfile = field(
        default_factory=LanguageProfile
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )

@dataclass(slots=True)
class PersonalityValidationError:
    """
    A single personality validation issue.
    """

    field: str

    message: str


@dataclass(slots=True)
class PersonalityValidationResult:
    """
    Result returned by the validator.
    """

    valid: bool

    errors: list[PersonalityValidationError] = field(
        default_factory=list
    )