from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta


class TokenManager:
    """
    Generates and validates access and refresh tokens.

    This implementation is storage-agnostic and is intended
    to work with the Session Manager in the next module.
    """

    def __init__(

        self,

        access_token_hours: int = 8,

        refresh_token_days: int = 30,

    ):

        self.access_token_hours = access_token_hours

        self.refresh_token_days = refresh_token_days

        self._access_tokens: dict[
            str,
            dict,
        ] = {}

        self._refresh_tokens: dict[
            str,
            dict,
        ] = {}

    # =====================================================
    # Token Generation
    # =====================================================

    def create_access_token(

        self,

        user_id: str,

        tenant_id: str | None = None,

    ) -> str:

        token = secrets.token_urlsafe(
            48
        )

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        self._access_tokens[
            token_hash
        ] = {

            "user_id": user_id,

            "tenant_id": tenant_id,

            "created_at": datetime.now(
                UTC
            ),

            "expires_at": (
                datetime.now(UTC)
                +
                timedelta(
                    hours=self.access_token_hours
                )
            ),

        }

        return token

    def create_refresh_token(

        self,

        user_id: str,

        tenant_id: str | None = None,

    ) -> str:

        token = secrets.token_urlsafe(
            64
        )

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        self._refresh_tokens[
            token_hash
        ] = {

            "user_id": user_id,

            "tenant_id": tenant_id,

            "created_at": datetime.now(
                UTC
            ),

            "expires_at": (
                datetime.now(UTC)
                +
                timedelta(
                    days=self.refresh_token_days
                )
            ),

        }

        return token

    # =====================================================
    # Validation
    # =====================================================

    def validate_access_token(

        self,

        token: str,

    ) -> bool:

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        data = self._access_tokens.get(
            token_hash
        )

        if data is None:

            return False

        return (
            datetime.now(UTC)
            <
            data["expires_at"]
        )

    def validate_refresh_token(

        self,

        token: str,

    ) -> bool:

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        data = self._refresh_tokens.get(
            token_hash
        )

        if data is None:

            return False

        return (
            datetime.now(UTC)
            <
            data["expires_at"]
        )

    # =====================================================
    # Information
    # =====================================================

    def access_token_data(

        self,

        token: str,

    ):

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        return self._access_tokens.get(
            token_hash
        )

    def refresh_token_data(

        self,

        token: str,

    ):

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        return self._refresh_tokens.get(
            token_hash
        )

    # =====================================================
    # Revocation
    # =====================================================

    def revoke_access_token(

        self,

        token: str,

    ) -> bool:

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        return (

            self._access_tokens.pop(
                token_hash,
                None,
            )

            is not None

        )

    def revoke_refresh_token(

        self,

        token: str,

    ) -> bool:

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        return (

            self._refresh_tokens.pop(
                token_hash,
                None,
            )

            is not None

        )

    def revoke_user_tokens(

        self,

        user_id: str,

    ):

        for token_hash, data in list(
            self._access_tokens.items()
        ):

            if data["user_id"] == user_id:

                del self._access_tokens[
                    token_hash
                ]

        for token_hash, data in list(
            self._refresh_tokens.items()
        ):

            if data["user_id"] == user_id:

                del self._refresh_tokens[
                    token_hash
                ]

    # =====================================================
    # Counts
    # =====================================================

    def access_token_count(self):

        return len(
            self._access_tokens
        )

    def refresh_token_count(self):

        return len(
            self._refresh_tokens
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "token_manager",

            "access_tokens": self.access_token_count(),

            "refresh_tokens": self.refresh_token_count(),

            "status": "healthy",

        }