from __future__ import annotations

import dns.exception
import dns.resolver


class DNSResolver:
    """
    Resolves public DNS records for custom-domain verification.

    This service has no tenant-awareness by design.

    Tenant security belongs to the Custom Domain repository/service.
    DNS resolution is simply an external verification mechanism.
    """

    def __init__(
        self,
        resolver: dns.resolver.Resolver | None = None,
    ):
        self.resolver = resolver or dns.resolver.Resolver()

    # =====================================================
    # TXT Records
    # =====================================================

    def get_txt_records(
        self,
        domain: str,
    ) -> list[str]:

        domain = self._normalize_domain(domain)

        try:
            answers = self.resolver.resolve(
                domain,
                "TXT",
            )
        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):
            return []

        records: list[str] = []

        for answer in answers:
            strings = getattr(
                answer,
                "strings",
                None,
            )

            if strings:
                records.append(
                    b"".join(strings).decode(
                        "utf-8",
                        errors="replace",
                    )
                )
            else:
                records.append(
                    str(answer).strip('"')
                )

        return records

    # =====================================================
    # TXT Verification
    # =====================================================

    def verify_txt(
        self,
        domain: str,
        expected_token: str,
    ) -> bool:

        expected_token = expected_token.strip()

        if not expected_token:
            raise ValueError(
                "Expected verification token is required."
            )

        verification_domain = (
            "_heshly-verification."
            + self._normalize_domain(domain)
        )

        records = self.get_txt_records(
            verification_domain
        )

        return expected_token in records

    # =====================================================
    # Verification Token
    # =====================================================

    def verify_heshly_token(
        self,
        domain: str,
        token: str,
    ) -> bool:

        return self.verify_txt(
            domain=domain,
            expected_token=token,
        )

    # =====================================================
    # Normalization
    # =====================================================

    @staticmethod
    def _normalize_domain(
        domain: str,
    ) -> str:

        domain = domain.strip().lower().rstrip(".")

        if not domain:
            raise ValueError(
                "Domain is required."
            )

        return domain
