from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class RoleAssignment:
    """
    Assignment of a role to a user.
    """

    assignment_id: str

    user_id: str

    role_id: str

    tenant_id: str

    assigned_by: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )