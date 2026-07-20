from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


# =====================================================
# Business Profile
# =====================================================

@dataclass(slots=True)
class BusinessProfile:
    """
    Public business identity profile.

    Stores customer-facing business information.
    """


    business_id: str

    name: str

    industry: str | None = None

    location: str | None = None


    # =================================================
    # Contact Details
    # =================================================

    email: str | None = None

    phone: str | None = None

    website: str | None = None

    address: str | None = None


    # =================================================
    # Additional Information
    # =================================================

    description: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    # =================================================
    # Update Helpers
    # =================================================

    def update_contact(
        self,
        email: str | None = None,
        phone: str | None = None,
        website: str | None = None,
        address: str | None = None,
    ):

        if email is not None:

            self.email = email


        if phone is not None:

            self.phone = phone


        if website is not None:

            self.website = website


        if address is not None:

            self.address = address


        self.updated_at = datetime.now(UTC)



    def update_location(
        self,
        location: str,
    ):

        self.location = location

        self.updated_at = datetime.now(UTC)



    def summary(self) -> dict:

        return {

            "business_id": self.business_id,

            "name": self.name,

            "industry": self.industry,

            "location": self.location,

            "email": self.email,

            "phone": self.phone,

        }