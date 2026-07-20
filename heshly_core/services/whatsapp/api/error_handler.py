from heshly_core.services.whatsapp.api.api_models import (
    CloudAPIError,
    CloudAPIErrorCategory,
    CloudAPIResponse,
)


class WhatsAppErrorHandler:
    """
    Converts raw HTTP responses into
    standardized CloudAPIError objects.
    """

    def handle(
        self,
        response: CloudAPIResponse,
    ) -> CloudAPIError:

        error = response.body.get(
            "error",
            {},
        )

        status = response.status_code

        category = CloudAPIErrorCategory.UNKNOWN

        retryable = False

        if status == 401:

            category = (
                CloudAPIErrorCategory.AUTHENTICATION
            )

        elif status == 403:

            category = (
                CloudAPIErrorCategory.AUTHORIZATION
            )

        elif status == 400:

            category = (
                CloudAPIErrorCategory.VALIDATION
            )

        elif status == 429:

            category = (
                CloudAPIErrorCategory.RATE_LIMIT
            )

            retryable = True

        elif status >= 500:

            category = (
                CloudAPIErrorCategory.SERVER
            )

            retryable = True

        elif status == 0:

            category = (
                CloudAPIErrorCategory.NETWORK
            )

            retryable = True

        return CloudAPIError(

            code=error.get(
                "code",
                -1,
            ),

            message=error.get(
                "message",
                "Unknown error.",
            ),

            category=category,

            retryable=retryable,

            error_type=error.get(
                "type"
            ),

            error_subcode=error.get(
                "error_subcode"
            ),

            fbtrace_id=error.get(
                "fbtrace_id"
            ),
        )