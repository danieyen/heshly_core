from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


# =====================================================
# IP Entry
# =====================================================

@dataclass(slots=True)
class IPEntry:
    """
    Represents an allow/deny rule for an IP address.
    """

    ip_address: str

    allowed: bool

    reason: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# =====================================================
# IP Access Control
# =====================================================

class IPAccessControl:
    """
    Maintains IP allow and deny lists.

    Rules:

    1. Deny list always wins.
    2. If allow list is empty,
       every IP not denied is allowed.
    3. If allow list has entries,
       only allowed IPs may connect.
    """

    def __init__(self):

        self._allow: dict[
            str,
            IPEntry,
        ] = {}

        self._deny: dict[
            str,
            IPEntry,
        ] = {}

    # =====================================================
    # Allow List
    # =====================================================

    def allow_ip(

        self,

        ip_address: str,

        reason: str = "",

    ) -> IPEntry:

        entry = IPEntry(

            ip_address=ip_address,

            allowed=True,

            reason=reason,

        )

        self._allow[ip_address] = entry

        self._deny.pop(
            ip_address,
            None,
        )

        return entry

    def remove_allowed_ip(

        self,

        ip_address: str,

    ) -> bool:

        return (

            self._allow.pop(
                ip_address,
                None,
            )

            is not None

        )

    # =====================================================
    # Deny List
    # =====================================================

    def deny_ip(

        self,

        ip_address: str,

        reason: str = "",

    ) -> IPEntry:

        entry = IPEntry(

            ip_address=ip_address,

            allowed=False,

            reason=reason,

        )

        self._deny[ip_address] = entry

        self._allow.pop(
            ip_address,
            None,
        )

        return entry

    def remove_denied_ip(

        self,

        ip_address: str,

    ) -> bool:

        return (

            self._deny.pop(
                ip_address,
                None,
            )

            is not None

        )

    # =====================================================
    # Validation
    # =====================================================

    def is_allowed(

        self,

        ip_address: str,

    ) -> bool:

        if ip_address in self._deny:

            return False

        if not self._allow:

            return True

        return ip_address in self._allow

    def is_denied(

        self,

        ip_address: str,

    ) -> bool:

        return ip_address in self._deny

    # =====================================================
    # Queries
    # =====================================================

    def list_allowed(self):

        return list(
            self._allow.values()
        )

    def list_denied(self):

        return list(
            self._deny.values()
        )

    # =====================================================
    # Management
    # =====================================================

    def clear(self):

        self._allow.clear()

        self._deny.clear()

    def health(self):

        return {

            "service": "ip_access_control",

            "allowed_ips": len(
                self._allow
            ),

            "denied_ips": len(
                self._deny
            ),

            "status": "healthy",

        }