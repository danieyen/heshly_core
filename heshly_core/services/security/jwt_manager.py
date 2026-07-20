from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta


class JWTManager:
    """
    Lightweight JWT (HS256) implementation.

    Uses only the Python standard library.
    """

    def __init__(
        self,
        secret: str,
        issuer: str = "heshly",
        expiry_hours: int = 8,
    ):

        self.secret = secret.encode()

        self.issuer = issuer

        self.expiry_hours = expiry_hours

    # =====================================================
    # Helpers
    # =====================================================

    def _b64_encode(
        self,
        value: bytes,
    ) -> str:

        return base64.urlsafe_b64encode(
            value
        ).rstrip(b"=").decode()

    def _b64_decode(
        self,
        value: str,
    ) -> bytes:

        padding = "=" * (
            -len(value) % 4
        )

        return base64.urlsafe_b64decode(
            value + padding
        )

    # =====================================================
    # Token Creation
    # =====================================================

    def create_token(
        self,
        user_id: str,
        tenant_id: str | None = None,
        extra: dict | None = None,
    ) -> str:

        now = datetime.now(UTC)

        header = {
            "alg": "HS256",
            "typ": "JWT",
        }

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "iss": self.issuer,
            "iat": int(now.timestamp()),
            "exp": int(
                (
                    now
                    + timedelta(
                        hours=self.expiry_hours
                    )
                ).timestamp()
            ),
        }

        if extra:

            payload.update(extra)

        header_b64 = self._b64_encode(
            json.dumps(
                header,
                separators=(",", ":"),
            ).encode()
        )

        payload_b64 = self._b64_encode(
            json.dumps(
                payload,
                separators=(",", ":"),
            ).encode()
        )

        message = (
            f"{header_b64}.{payload_b64}"
        ).encode()

        signature = hmac.new(
            self.secret,
            message,
            hashlib.sha256,
        ).digest()

        signature_b64 = self._b64_encode(
            signature
        )

        return (
            f"{header_b64}."
            f"{payload_b64}."
            f"{signature_b64}"
        )

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        token: str,
    ) -> bool:

        try:

            header_b64, payload_b64, signature = (
                token.split(".")
            )

        except ValueError:

            return False

        message = (
            f"{header_b64}.{payload_b64}"
        ).encode()

        expected = self._b64_encode(

            hmac.new(
                self.secret,
                message,
                hashlib.sha256,
            ).digest()

        )

        if not hmac.compare_digest(
            signature,
            expected,
        ):

            return False

        payload = json.loads(

            self._b64_decode(
                payload_b64
            )

        )

        return (
            datetime.now(UTC).timestamp()
            <
            payload["exp"]
        )

    # =====================================================
    # Payload
    # =====================================================

    def payload(
        self,
        token: str,
    ) -> dict:

        return json.loads(

            self._b64_decode(
                token.split(".")[1]
            )

        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "jwt_manager",

            "issuer": self.issuer,

            "status": "healthy",

        }