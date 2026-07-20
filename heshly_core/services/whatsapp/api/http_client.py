from __future__ import annotations

import json

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)

from heshly_core.services.whatsapp.api.api_models import (
    CloudAPIRequest,
    CloudAPIResponse,
)

from heshly_core.services.whatsapp.api.authentication import (
    WhatsAppAuthentication,
)


class WhatsAppHTTPClient:
    """
    Executes HTTP requests against
    the WhatsApp Cloud API.

    This class is the ONLY component
    responsible for network I/O.
    """

    BASE_URL = "https://graph.facebook.com"

    def __init__(self) -> None:
        self._authentication = (
            WhatsAppAuthentication()
        )

    def send(
        self,
        configuration: WhatsAppConfiguration,
        request: CloudAPIRequest,
        timeout: int = 30,
    ) -> CloudAPIResponse:

        url = (
            self.BASE_URL
            + request.endpoint
        )

        headers = (
            self._authentication.build_headers(
                configuration
            )
        )

        headers.update(
            request.headers
        )

        data = json.dumps(
            request.payload
        ).encode("utf-8")

        http_request = Request(
            url=url,
            data=data,
            headers=headers,
            method=request.method,
        )

        try:

            with urlopen(
                http_request,
                timeout=timeout,
            ) as response:

                body = response.read().decode(
                    "utf-8"
                )

                return CloudAPIResponse(
                    status_code=response.status,
                    body=(
                        json.loads(body)
                        if body
                        else {}
                    ),
                    headers=dict(
                        response.headers
                    ),
                )

        except HTTPError as exc:

            body = exc.read().decode(
                "utf-8"
            )

            return CloudAPIResponse(
                status_code=exc.code,
                body=(
                    json.loads(body)
                    if body
                    else {}
                ),
                headers=dict(
                    exc.headers
                ),
            )

        except URLError as exc:

            return CloudAPIResponse(
                status_code=0,
                body={
                    "error": {
                        "message": str(
                            exc.reason
                        ),
                        "code": -1,
                        "type": "NetworkError",
                    }
                },
                headers={},
            )