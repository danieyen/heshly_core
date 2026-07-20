from __future__ import annotations

from heshly_core.models.business_account import (
    BusinessAccount,
)


class BusinessRepository:
    """
    Shared in-memory Business Repository.

    Future:
    ERPNext / Database persistence
    """


    _businesses: dict[str, BusinessAccount] = {}


    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        business: BusinessAccount,
    ) -> BusinessAccount:


        self._businesses[
            business.business_id
        ] = business


        return business



    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        business_id: str,
    ) -> BusinessAccount | None:


        return self._businesses.get(
            business_id
        )



    # =====================================================
    # All
    # =====================================================

    def all(self) -> list[BusinessAccount]:

        return list(
            self._businesses.values()
        )



    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        business_id: str,
    ):


        self._businesses.pop(
            business_id,
            None,
        )



    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self._businesses.clear()



    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "repository":
                "business_repository",

            "status":
                "healthy",

            "records":
                len(self._businesses),

        }