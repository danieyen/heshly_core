from __future__ import annotations

from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.auth.authentication_service import (
    AuthenticationService,
)


class LoginManager:
    """
    Handles user login/logout operations.
    """

    def __init__(
        self,
        authentication_service: AuthenticationService,
    ):

        self.authentication_service = (
            authentication_service
        )

        self.current_user: AuthUser | None = None


    # =====================================================
    # Login
    # =====================================================

    def login(
        self,
        email: str,
        password: str,
    ) -> AuthUser | None:

        user = self.authentication_service.authenticate(

            email,

            password,

        )

        if user is not None:

            self.current_user = user

        return user


    # =====================================================
    # Logout
    # =====================================================

    def logout(self):

        self.current_user = None


    # =====================================================
    # Current User
    # =====================================================

    def get_current_user(self):

        return self.current_user


    # =====================================================
    # Authentication Status
    # =====================================================

    def is_authenticated(self) -> bool:

        return self.current_user is not None


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "login_manager",

            "authenticated":
                self.is_authenticated(),

            "status": "healthy",

        }