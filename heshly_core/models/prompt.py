from dataclasses import dataclass, field
from enum import Enum


class ResponseType(str, Enum):
    TEXT = "text"
    QUESTION = "question"
    CONFIRMATION = "confirmation"
    ERROR = "error"


class ResponseTone(str, Enum):
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    FORMAL = "formal"
    CASUAL = "casual"


class ResponseChannel(str, Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    WEB = "web"
    EMAIL = "email"
    VOICE = "voice"


@dataclass(slots=True)
class PromptContext:
    system_prompt: str = ""
    business_context: str = ""
    memory_context: str = ""
    conversation_context: str = ""


@dataclass(slots=True)
class PromptRequest:
    customer_message: str
    context: PromptContext
    tone: ResponseTone = ResponseTone.FRIENDLY


@dataclass(slots=True)
class PromptResponse:
    message: str
    response_type: ResponseType = ResponseType.TEXT
    confidence: float = 1.0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ValidationResult:
    """
    Result of validating an AI response.
    """

    valid: bool = True

    errors: list[str] = field(
        default_factory=list
    )