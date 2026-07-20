from __future__ import annotations

from heshly_core.models.channel_route import (
    ChannelRoute,
)


class ChannelRouteRepository:

    def __init__(self):

        self._routes: dict[
            tuple[str, str],
            ChannelRoute,
        ] = {}

    def save(
        self,
        route: ChannelRoute,
    ) -> ChannelRoute:

        key = (
            route.tenant_id,
            route.event,
        )

        self._routes[key] = route

        return route

    def get(
        self,
        tenant_id: str,
        event: str,
    ) -> ChannelRoute | None:

        return self._routes.get(
            (
                tenant_id,
                event,
            )
        )