from __future__ import annotations

from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.auth.password_manager import (
    PasswordManager,
)


class AuthenticationService:
    """
    Handles user authentication.
    """

    def __init__(self):

        self.passwords = PasswordManager()

        self.users: dict[str, AuthUser] = {}


    # =====================================================
    # Register User
    # =====================================================

    def register(
        self,
        user: AuthUser,
        password: str,
    ) -> AuthUser:

        valid, message = (
            self.passwords.validate_strength(
                password
            )
        )

        if not valid:

            raise ValueError(message)

        user.password_hash = (
            self.passwords.hash_password(
                password
            )
        )

        self.users[user.email] = user

        return user


    # =====================================================
    # Authenticate
    # =====================================================

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> AuthUser | None:

        user = self.users.get(
            email
        )

        if user is None:

            return None

        if not user.is_active:

            return None

        if not self.passwords.verify_password(

            password,

            user.password_hash,

        ):

            return None

        user.record_login()

        return user


    # =====================================================
    # Get User
    # =====================================================

    def get_user(
        self,
        email: str,
    ) -> AuthUser | None:

        return self.users.get(
            email
        )


    # =====================================================
    # Logout
    # =====================================================

    def logout(
        self,
        email: str,
    ) -> bool:

        return (
            email
            in
            self.users
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "authentication_service",

            "users":
                len(self.users),

            "status":
                "healthy",

        }