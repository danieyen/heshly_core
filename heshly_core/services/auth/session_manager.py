from __future__ import annotations

import secrets

from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.models.session import (
    UserSession,
)


class SessionManager:
    """
    Manages authenticated sessions.
    """

    def __init__(self):

        self.sessions: dict[str, UserSession] = {}


    # =====================================================
    # Create Session
    # =====================================================

    def create_session(
        self,
        user: AuthUser,
    ) -> UserSession:

        session = UserSession(

            session_id=secrets.token_hex(16),

            user_id=user.user_id,

            tenant_id=user.tenant_id,

        )

        self.sessions[
            session.session_id
        ] = session

        return session


    # =====================================================
    # Get Session
    # =====================================================

    def get_session(
        self,
        session_id: str,
    ) -> UserSession | None:

        session = self.sessions.get(
            session_id
        )

        if session is None:

            return None

        if session.is_expired:

            self.destroy_session(
                session_id
            )

            return None

        return session


    # =====================================================
    # Destroy Session
    # =====================================================

    def destroy_session(
        self,
        session_id: str,
    ) -> bool:

        return (

            self.sessions.pop(
                session_id,
                None,
            )

            is not None

        )


    # =====================================================
    # Validate Session
    # =====================================================

    def validate(
        self,
        session_id: str,
    ) -> bool:

        return (

            self.get_session(
                session_id
            )

            is not None

        )


    # =====================================================
    # Active Sessions
    # =====================================================

    def active_sessions(self) -> int:

        return len(
            self.sessions
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "session_manager",

            "active_sessions": len(
                self.sessions
            ),

            "status": "healthy",

        }