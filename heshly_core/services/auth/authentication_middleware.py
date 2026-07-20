from __future__ import annotations

from heshly_core.models.auth import (
    AuthUser,
)


class AuthenticationMiddleware:
    """
    Handles API authentication.

    MVP implementation:
    token lookup.

    Future:
    JWT/OAuth2/API keys.
    """

    def __init__(self):

        self.tokens = {}


    # =====================================================
    # Register Token
    # =====================================================

    def register_token(
        self,
        token: str,
        user: AuthUser,
    ):

        self.tokens[token] = user


    # =====================================================
    # Authenticate
    # =====================================================

    def authenticate(
        self,
        token: str,
    ) -> AuthUser | None:

        return self.tokens.get(
            token
        )


    # =====================================================
    # Require Authentication
    # =====================================================

    def require(
        self,
        token: str,
    ) -> AuthUser:

        user = self.authenticate(
            token
        )

        if user is None:

            raise PermissionError(
                "Invalid authentication token"
            )

        return user


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "authentication_middleware",

            "status":
                "healthy",

        }