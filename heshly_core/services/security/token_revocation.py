from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import hashlib


# =====================================================
# Revoked Token
# =====================================================

@dataclass(slots=True)
class RevokedToken:
    """
    Represents a revoked access or refresh token.
    """

    token_hash: str

    user_id: str

    tenant_id: str | None = None

    reason: str = ""

    revoked_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# =====================================================
# Token Revocation Service
# =====================================================

class TokenRevocation:
    """
    Maintains a revocation list (blacklist)
    for access and refresh tokens.

    This service is independent of the
    TokenManager and JWTManager so that
    every authentication provider can
    consult a single revocation source.
    """

    def __init__(self):

        self._tokens: dict[
            str,
            RevokedToken,
        ] = {}

    # =====================================================
    # Internal
    # =====================================================

    def _hash(
        self,
        token: str,
    ) -> str:

        return hashlib.sha256(
            token.encode()
        ).hexdigest()

    # =====================================================
    # Revocation
    # =====================================================

    def revoke(

        self,

        token: str,

        user_id: str,

        tenant_id: str | None = None,

        reason: str = "",

    ) -> RevokedToken:

        token_hash = self._hash(
            token
        )

        revoked = RevokedToken(

            token_hash=token_hash,

            user_id=user_id,

            tenant_id=tenant_id,

            reason=reason,

        )

        self._tokens[
            token_hash
        ] = revoked

        return revoked

    # =====================================================
    # Validation
    # =====================================================

    def is_revoked(
        self,
        token: str,
    ) -> bool:

        return (

            self._hash(token)

            in

            self._tokens

        )

    # =====================================================
    # Queries
    # =====================================================

    def get(
        self,
        token: str,
    ) -> RevokedToken | None:

        return self._tokens.get(
            self._hash(token)
        )

    def list(self):

        return list(
            self._tokens.values()
        )

    def list_by_user(
        self,
        user_id: str,
    ):

        return [

            token

            for token

            in self._tokens.values()

            if token.user_id == user_id

        ]

    # =====================================================
    # Removal
    # =====================================================

    def remove(
        self,
        token: str,
    ) -> bool:

        return (

            self._tokens.pop(
                self._hash(token),
                None,
            )

            is not None

        )

    def clear(self):

        self._tokens.clear()

    # =====================================================
    # Counts
    # =====================================================

    def count(self):

        return len(
            self._tokens
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "token_revocation",

            "revoked_tokens": self.count(),

            "status": "healthy",

        }