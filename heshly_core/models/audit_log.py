from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# =====================================================
# Audit Event Type
# =====================================================

class AuditEventType(str, Enum):

    CREATE = "create"

    READ = "read"

    UPDATE = "update"

    DELETE = "delete"

    LOGIN = "login"

    LOGOUT = "logout"

    ACCESS_DENIED = "access_denied"

    SECURITY = "security"

    SYSTEM = "system"


# =====================================================
# Audit Severity
# =====================================================

class AuditSeverity(str, Enum):

    INFO = "info"

    WARNING = "warning"

    ERROR = "error"

    CRITICAL = "critical"


# =====================================================
# Audit Log
# =====================================================

@dataclass(slots=True)
class AuditLog:
    """
    Immutable record of system activity.

    Used for:
    - security tracking
    - compliance reporting
    - debugging
    - user activity history
    """

    audit_id: str

    tenant_id: str | None

    user_id: str | None

    event_type: AuditEventType

    action: str

    resource: str

    severity: AuditSeverity = (
        AuditSeverity.INFO
    )

    description: str = ""

    ip_address: str | None = None

    user_agent: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    # =================================================
    # Helpers
    # =================================================

    @property
    def is_security_event(self) -> bool:

        return (
            self.event_type
            ==
            AuditEventType.SECURITY
        )


    @property
    def is_failure(self) -> bool:

        return self.severity in (

            AuditSeverity.ERROR,

            AuditSeverity.CRITICAL,

        )