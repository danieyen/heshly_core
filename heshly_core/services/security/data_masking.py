from __future__ import annotations

import re


class DataMasking:
    """
    Masks sensitive information before it
    is displayed or written to logs.
    """

    # =====================================================
    # Email
    # =====================================================

    def mask_email(
        self,
        email: str,
    ) -> str:

        if "@" not in email:

            return email

        local, domain = email.split(
            "@",
            1,
        )

        if len(local) <= 2:

            masked = "*" * len(local)

        else:

            masked = (
                local[:2]
                + "*" * (len(local) - 2)
            )

        return f"{masked}@{domain}"

    # =====================================================
    # Phone
    # =====================================================

    def mask_phone(
        self,
        phone: str,
    ) -> str:

        digits = re.sub(
            r"\D",
            "",
            phone,
        )

        if len(digits) <= 4:

            return "*" * len(digits)

        return (
            "*" * (len(digits) - 4)
            + digits[-4:]
        )

    # =====================================================
    # API Keys
    # =====================================================

    def mask_api_key(
        self,
        value: str,
    ) -> str:

        if len(value) <= 8:

            return "*" * len(value)

        return (
            value[:4]
            + "*" * (len(value) - 8)
            + value[-4:]
        )

    # =====================================================
    # Generic Secret
    # =====================================================

    def mask_secret(
        self,
        value: str,
    ) -> str:

        return "*" * len(value)

    # =====================================================
    # Dictionary
    # =====================================================

    def mask_dictionary(
        self,
        data: dict,
        fields: set[str] | None = None,
    ) -> dict:

        if fields is None:

            fields = {

                "password",

                "token",

                "secret",

                "api_key",

                "access_token",

                "refresh_token",

            }

        masked = {}

        for key, value in data.items():

            if (

                key in fields

                and

                isinstance(
                    value,
                    str,
                )

            ):

                masked[key] = self.mask_secret(
                    value
                )

            else:

                masked[key] = value

        return masked

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "data_masking",

            "status": "healthy",

        }