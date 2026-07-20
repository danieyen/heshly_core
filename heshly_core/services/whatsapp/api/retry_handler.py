import time

from heshly_core.services.whatsapp.api.api_models import (
    CloudAPIError,
)


class WhatsAppRetryHandler:
    """
    Handles retry logic for retryable
    WhatsApp Cloud API errors.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
    ) -> None:

        self.max_attempts = max_attempts

        self.initial_delay = initial_delay

        self.backoff_multiplier = backoff_multiplier

    def should_retry(
        self,
        error: CloudAPIError,
        attempt: int,
    ) -> bool:
        """
        Determines whether another retry
        should be attempted.
        """

        return (

            error.retryable

            and attempt < self.max_attempts

        )

    def wait(
        self,
        attempt: int,
    ) -> None:
        """
        Waits using exponential backoff.
        """

        delay = (

            self.initial_delay

            * (self.backoff_multiplier ** (attempt - 1))

        )

        time.sleep(delay)