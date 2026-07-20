from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


# =====================================================
# Refresh Token
# =====================================================

@dataclass(slots=True)
class RefreshToken:

    token: str

    user_id: str

    tenant_id: str | None = None

    session_id: str | None = None

    issued_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    expires_at: datetime = field(
        default_factory=lambda: (
            datetime.now(UTC)
            + timedelta(days=30)
        )
    )

    revoked: bool = False

    rotated_from: str | None = None

    @property
    def is_expired(self) -> bool:

        return (
            datetime.now(UTC)
            >=
            self.expires_at
        )

    @property
    def is_valid(self) -> bool:

        return (
            not self.revoked
            and
            not self.is_expired
        )


# =====================================================
# Refresh Token Manager
# =====================================================

class RefreshTokenManager:

    """
    Handles refresh token lifecycle.
    """

    def __init__(

        self,

        expiry_days: int = 30,

    ):

        self.expiry_days = expiry_days

        self._tokens: dict[
            str,
            RefreshToken,
        ] = {}

    # =====================================================
    # Create
    # =====================================================

    def issue(

        self,

        user_id: str,

        tenant_id: str | None = None,

        session_id: str | None = None,

    ) -> RefreshToken:

        token = RefreshToken(

            token=secrets.token_urlsafe(
                64
            ),

            user_id=user_id,

            tenant_id=tenant_id,

            session_id=session_id,

            expires_at=(

                datetime.now(UTC)

                +

                timedelta(
                    days=self.expiry_days
                )

            ),

        )

        self._tokens[
            token.token
        ] = token

        return token

    # =====================================================
    # Validation
    # =====================================================

    def validate(

        self,

        token: str,

    ) -> bool:

        stored = self._tokens.get(
            token
        )

        if stored is None:

            return False

        return stored.is_valid

    # =====================================================
    # Lookup
    # =====================================================

    def get(

        self,

        token: str,

    ) -> RefreshToken | None:

        return self._tokens.get(
            token
        )

    # =====================================================
    # Rotation
    # =====================================================

    def rotate(

        self,

        token: str,

    ) -> RefreshToken | None:

        current = self.get(
            token
        )

        if current is None:

            return None

        if not current.is_valid:

            return None

        current.revoked = True

        replacement = self.issue(

            user_id=current.user_id,

            tenant_id=current.tenant_id,

            session_id=current.session_id,

        )

        replacement.rotated_from = (
            current.token
        )

        return replacement

    # =====================================================
    # Revocation
    # =====================================================

    def revoke(

        self,

        token: str,

    ) -> bool:

        stored = self.get(
            token
        )

        if stored is None:

            return False

        stored.revoked = True

        return True

    def revoke_user_tokens(

        self,

        user_id: str,

    ):

        for token in self._tokens.values():

            if token.user_id == user_id:

                token.revoked = True

    # =====================================================
    # Cleanup
    # =====================================================

    def cleanup(self):

        expired = [

            token

            for token, data

            in self._tokens.items()

            if data.is_expired

        ]

        for token in expired:

            del self._tokens[token]

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "refresh_token_manager",

            "tokens": len(
                self._tokens
            ),

            "status": "healthy",

        }