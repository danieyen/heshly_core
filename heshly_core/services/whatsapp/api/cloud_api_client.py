from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
    WhatsAppMessage,
)

from heshly_core.services.whatsapp.api.api_models import (
    CloudAPIError,
    CloudAPISuccess,
)

from heshly_core.services.whatsapp.api.http_client import (
    WhatsAppHTTPClient,
)

from heshly_core.services.whatsapp.api.request_builder import (
    WhatsAppRequestBuilder,
)

from heshly_core.services.whatsapp.api.response_parser import (
    WhatsAppResponseParser,
)

from heshly_core.services.whatsapp.api.error_handler import (
    WhatsAppErrorHandler,
)

from heshly_core.services.whatsapp.api.retry_handler import (
    WhatsAppRetryHandler,
)


class WhatsAppCloudAPIClient:
    """
    High-level client for the
    WhatsApp Cloud API.
    """

    def __init__(self) -> None:

        self._builder = WhatsAppRequestBuilder()

        self._http = WhatsAppHTTPClient()

        self._parser = WhatsAppResponseParser()

        self._errors = WhatsAppErrorHandler()

        self._retry = WhatsAppRetryHandler()

    def send_message(
        self,
        configuration: WhatsAppConfiguration,
        message: WhatsAppMessage,
    ) -> CloudAPISuccess | CloudAPIError:
        """
        Sends a WhatsApp message using the
        Cloud API with automatic retries.
        """

        attempt = 1

        while True:

            request = (
                self._builder
                .build_send_message_request(
                    configuration,
                    message,
                )
            )

            response = self._http.send(
                configuration,
                request,
            )

            if 200 <= response.status_code < 300:

                return (
                    self._parser
                    .parse_send_message_response(
                        response
                    )
                )

            error = self._errors.handle(
                response
            )

            if not self._retry.should_retry(
                error,
                attempt,
            ):

                return error

            self._retry.wait(
                attempt
            )

            attempt += 1