from __future__ import annotations

from heshly_core.models.calendar import (
    CalendarProvider,
)

from heshly_core.services.calendar.providers.provider_interface import (
    CalendarProviderInterface,
)

from heshly_core.services.calendar.providers.erpnext_provider import (
    ERPNextCalendarProvider,
)

from heshly_core.services.calendar.providers.google_calendar_provider import (
    GoogleCalendarProvider,
)

from heshly_core.services.calendar.providers.outlook_provider import (
    OutlookCalendarProvider,
)


class ProviderFactory:
    """
    Factory responsible for creating
    calendar provider implementations.
    """

    def create(
        self,
        provider: CalendarProvider,
    ) -> CalendarProviderInterface:

        if provider == CalendarProvider.ERPNEXT:

            return ERPNextCalendarProvider()

        if provider == CalendarProvider.GOOGLE:

            return GoogleCalendarProvider()

        if provider == CalendarProvider.OUTLOOK:

            return OutlookCalendarProvider()

        raise ValueError(
            f"Unsupported calendar provider: {provider}"
        )