from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class APIEndpoint:

    path: str

    method: str

    description: str

    permissions: list[str] = field(
        default_factory=list
    )


@dataclass(slots=True)
class APIDocumentation:

    version: str

    title: str = "Heshly API"

    endpoints: list[APIEndpoint] = field(
        default_factory=list
    )


    def add_endpoint(
        self,
        endpoint: APIEndpoint,
    ):

        self.endpoints.append(
            endpoint
        )