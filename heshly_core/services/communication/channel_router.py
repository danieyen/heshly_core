from __future__ import annotations

from heshly_core.models.channel_route import (
    ChannelRoute,
    CommunicationChannel,
)

from heshly_core.repositories.channel_route_repository import (
    ChannelRouteRepository,
)


class ChannelRouter:
    """
    Tenant Communication Channel Router.
    """

    def __init__(self):

        self.repository = (
            ChannelRouteRepository()
        )

    def register(
        self,
        route: ChannelRoute,
    ) -> ChannelRoute:

        return self.repository.save(
            route
        )

    def resolve(
        self,
        tenant_id: str,
        event: str,
    ) -> CommunicationChannel | None:

        route = self.repository.get(
            tenant_id,
            event,
        )

        if route is None:

            return None

        if not route.enabled:

            return None

        return route.preferred_channel

    def fallback_channels(
        self,
        tenant_id: str,
        event: str,
    ) -> list[CommunicationChannel]:

        route = self.repository.get(
            tenant_id,
            event,
        )

        if route is None:

            return []

        return route.fallback_channels

    def health(self):

        return {

            "service": "channel_router",

            "status": "healthy",

        }