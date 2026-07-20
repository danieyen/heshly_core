from __future__ import annotations

import hashlib
import secrets
import string


class PasswordManager:
    """
    Handles password hashing and validation.
    """

    def __init__(self):

        self.algorithm = "sha256"

    # =====================================================
    # Hash Password
    # =====================================================

    def hash_password(
        self,
        password: str,
    ) -> str:

        salt = secrets.token_hex(16)

        digest = hashlib.sha256(
            f"{salt}{password}".encode("utf-8")
        ).hexdigest()

        return f"{salt}${digest}"

    # =====================================================
    # Verify Password
    # =====================================================

    def verify_password(
        self,
        password: str,
        password_hash: str,
    ) -> bool:

        try:

            salt, stored_hash = (
                password_hash.split("$", 1)
            )

        except ValueError:

            return False

        digest = hashlib.sha256(
            f"{salt}{password}".encode("utf-8")
        ).hexdigest()

        return secrets.compare_digest(
            digest,
            stored_hash,
        )

    # =====================================================
    # Password Strength
    # =====================================================

    def validate_strength(
        self,
        password: str,
    ) -> tuple[bool, str]:

        if len(password) < 8:

            return (
                False,
                "Password must be at least 8 characters.",
            )

        if not any(
            c.isupper()
            for c in password
        ):

            return (
                False,
                "Password must contain an uppercase letter.",
            )

        if not any(
            c.islower()
            for c in password
        ):

            return (
                False,
                "Password must contain a lowercase letter.",
            )

        if not any(
            c.isdigit()
            for c in password
        ):

            return (
                False,
                "Password must contain a digit.",
            )

        if not any(
            c in string.punctuation
            for c in password
        ):

            return (
                False,
                "Password must contain a special character.",
            )

        return (
            True,
            "Strong password.",
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "password_manager",

            "status": "healthy",

            "algorithm": self.algorithm,

        }