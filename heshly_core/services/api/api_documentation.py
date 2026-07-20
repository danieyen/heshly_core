from __future__ import annotations

from heshly_core.models.api_documentation import (
    APIEndpoint,
    APIDocumentation,
)


class APIDocumentationService:
    """
    Maintains Heshly API documentation.
    """

    def __init__(self):

        self.documentation = (
            APIDocumentation(
                version="v1"
            )
        )


    # =====================================================
    # Register Endpoint
    # =====================================================

    def register_endpoint(
        self,
        path: str,
        method: str,
        description: str,
        permissions: list[str] | None = None,
    ):

        endpoint = APIEndpoint(

            path=path,

            method=method,

            description=description,

            permissions=
                permissions or [],

        )


        self.documentation.add_endpoint(
            endpoint
        )


    # =====================================================
    # Get Documentation
    # =====================================================

    def get_documentation(self):

        return self.documentation


    # =====================================================
    # List Endpoints
    # =====================================================

    def endpoints(self):

        return (
            self.documentation.endpoints
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "api_documentation",

            "status":
                "healthy",

        }