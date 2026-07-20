from __future__ import annotations

import re
from dataclasses import dataclass, field

from heshly_core.models.crm import Lead


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.valid


class LeadValidator:
    """Validates Lead objects before they are saved or updated."""

    PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")
    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    def validate(self, lead: Lead) -> ValidationResult:
        errors: list[str] = []

        # --------------------------------------------------
        # Required Fields
        # --------------------------------------------------

        if not lead.lead_id.strip():
            errors.append("Lead ID is required.")

        if not lead.business_id.strip():
            errors.append("Business ID is required.")

        if not lead.full_name.strip():
            errors.append("Customer name is required.")

        # --------------------------------------------------
        # Phone
        # --------------------------------------------------

        if lead.phone:
            phone = lead.phone.strip()

            if not self.PHONE_PATTERN.fullmatch(phone):
                errors.append("Invalid phone number.")

        # --------------------------------------------------
        # Email
        # --------------------------------------------------

        if lead.email:
            email = lead.email.strip()

            if not self.EMAIL_PATTERN.fullmatch(email):
                errors.append("Invalid email address.")

        # --------------------------------------------------
        # Score
        # --------------------------------------------------

        if lead.score < 0 or lead.score > 100:
            errors.append("Lead score must be between 0 and 100.")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
        )