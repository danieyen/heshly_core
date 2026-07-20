from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


# =====================================================
# Locked Account
# =====================================================

@dataclass(slots=True)
class LockedAccount:

    user_id: str

    reason: str = "Too many failed login attempts"

    locked_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    locked_until: datetime = field(
        default_factory=lambda: (
            datetime.now(UTC)
            + timedelta(minutes=15)
        )
    )


# =====================================================
# Account Lockout Manager
# =====================================================

class AccountLockout:
    """
    Manages temporary account lockouts.
    """

    def __init__(

        self,

        lockout_minutes: int = 15,

    ):

        self.lockout_minutes = lockout_minutes

        self._locked_accounts: dict[
            str,
            LockedAccount,
        ] = {}

    # =====================================================
    # Lock
    # =====================================================

    def lock(

        self,

        user_id: str,

        reason: str = "Too many failed login attempts",

    ) -> LockedAccount:

        account = LockedAccount(

            user_id=user_id,

            reason=reason,

            locked_at=datetime.now(UTC),

            locked_until=(

                datetime.now(UTC)

                +

                timedelta(
                    minutes=self.lockout_minutes
                )

            ),

        )

        self._locked_accounts[
            user_id
        ] = account

        return account

    # =====================================================
    # Unlock
    # =====================================================

    def unlock(

        self,

        user_id: str,

    ) -> bool:

        return (

            self._locked_accounts.pop(
                user_id,
                None,
            )

            is not None

        )

    # =====================================================
    # Status
    # =====================================================

    def is_locked(

        self,

        user_id: str,

    ) -> bool:

        account = self._locked_accounts.get(
            user_id
        )

        if account is None:

            return False

        if datetime.now(UTC) >= account.locked_until:

            self.unlock(
                user_id
            )

            return False

        return True

    def get(

        self,

        user_id: str,

    ) -> LockedAccount | None:

        return self._locked_accounts.get(
            user_id
        )

    def remaining_lock_time(

        self,

        user_id: str,

    ) -> int:

        account = self.get(
            user_id
        )

        if account is None:

            return 0

        seconds = int(

            (

                account.locked_until

                -

                datetime.now(UTC)

            ).total_seconds()

        )

        return max(
            seconds,
            0,
        )

    # =====================================================
    # Management
    # =====================================================

    def clear(self):

        self._locked_accounts.clear()

    def count(self):

        return len(
            self._locked_accounts
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "account_lockout",

            "locked_accounts": self.count(),

            "status": "healthy",

        }