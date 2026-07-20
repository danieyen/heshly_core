from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CloudAPIErrorCategory(str, Enum):
    """
    Classification of Cloud API errors.
    """

    AUTHENTICATION = "authentication"

    AUTHORIZATION = "authorization"

    VALIDATION = "validation"

    RATE_LIMIT = "rate_limit"

    NETWORK = "network"

    SERVER = "server"

    UNKNOWN = "unknown"


@dataclass(slots=True)
class CloudAPIRequest:
    """
    Generic request sent to the
    WhatsApp Cloud API.
    """

    method: str

    endpoint: str

    payload: dict[str, Any] = field(
        default_factory=dict
    )

    headers: dict[str, str] = field(
        default_factory=dict
    )

    params: dict[str, str] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class CloudAPIResponse:
    """
    Generic HTTP response.
    """

    status_code: int

    body: dict[str, Any]

    headers: dict[str, str] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class CloudAPIError:
    """
    Standardized Cloud API error.
    """

    code: int

    message: str

    category: CloudAPIErrorCategory

    retryable: bool

    error_type: str | None = None

    error_subcode: int | None = None

    fbtrace_id: str | None = None


@dataclass(slots=True)
class CloudAPISuccess:
    """
    Successful API operation.
    """

    success: bool

    message_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )