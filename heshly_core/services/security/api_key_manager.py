from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from heshly_core.models.api_key import (
    APIKey,
    APIKeyScope,
)
from heshly_core.repositories.api_key_repository import (
    APIKeyRepository,
)


class APIKeyManager:
    """
    Creates, validates and manages API keys.
    """

    def __init__(
        self,
        repository: APIKeyRepository,
    ):

        self.repository = repository

    # =====================================================
    # Internal
    # =====================================================

    def _generate_secret(self) -> str:

        return secrets.token_urlsafe(32)

    def _hash(
        self,
        value: str,
    ) -> str:

        return hashlib.sha256(
            value.encode()
        ).hexdigest()

    # =====================================================
    # Create
    # =====================================================

    def create_key(
        self,
        key_id: str,
        tenant_id: str,
        name: str,
        scope: APIKeyScope = APIKeyScope.FULL,
        created_by: str | None = None,
        expires_in_days: int | None = None,
    ) -> tuple[APIKey, str]:

        secret = self._generate_secret()

        hashed = self._hash(
            secret
        )

        expires_at = None

        if expires_in_days is not None:

            expires_at = (
                datetime.now(UTC)
                + timedelta(days=expires_in_days)
            )

        key = APIKey(

            key_id=key_id,

            tenant_id=tenant_id,

            name=name,

            key_hash=hashed,

            scope=scope,

            created_by=created_by,

            expires_at=expires_at,

        )

        self.repository.save(
            key
        )

        return key, secret

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        secret: str,
    ) -> APIKey | None:

        hashed = self._hash(
            secret
        )

        key = self.repository.get_by_hash(
            hashed
        )

        if key is None:

            return None

        if not key.is_active:

            return None

        if key.is_expired:

            key.expire()

            self.repository.save(
                key
            )

            return None

        key.mark_used()

        self.repository.save(
            key
        )

        return key

    # =====================================================
    # Lifecycle
    # =====================================================

    def disable(
        self,
        key_id: str,
    ) -> bool:

        key = self.repository.get(
            key_id
        )

        if key is None:

            return False

        key.disable()

        self.repository.save(
            key
        )

        return True

    def enable(
        self,
        key_id: str,
    ) -> bool:

        key = self.repository.get(
            key_id
        )

        if key is None:

            return False

        key.enable()

        self.repository.save(
            key
        )

        return True

    def revoke(
        self,
        key_id: str,
    ) -> bool:

        key = self.repository.get(
            key_id
        )

        if key is None:

            return False

        key.revoke()

        self.repository.save(
            key
        )

        return True

    # =====================================================
    # Queries
    # =====================================================

    def tenant_keys(
        self,
        tenant_id: str,
    ) -> list[APIKey]:

        return self.repository.list_by_tenant(
            tenant_id
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "api_key_manager",

            "keys": self.repository.count(),

            "active_keys": len(
                self.repository.list_active()
            ),

            "status": "healthy",

        }