from __future__ import annotations

import frappe

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    BillingCycle,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class FrappeSubscriptionRepository(
    BaseRepository[Subscription]
):
    """
    Persistent tenant-aware Subscription repository.

    tenant_id is the security boundary.
    business_id identifies the business inside that tenant.
    subscription_id identifies the subscription.
    """

    DOCTYPE = "Heshly Subscription"

    STATUS_TO_FRAPPE = {
        SubscriptionStatus.TRIAL: "Trial",
        SubscriptionStatus.ACTIVE: "Active",
        SubscriptionStatus.PAST_DUE: "Past Due",
        SubscriptionStatus.SUSPENDED: "Suspended",
        SubscriptionStatus.CANCELLED: "Cancelled",
        SubscriptionStatus.EXPIRED: "Expired",
    }

    STATUS_FROM_FRAPPE = {
        "Trial": SubscriptionStatus.TRIAL,
        "Active": SubscriptionStatus.ACTIVE,
        "Past Due": SubscriptionStatus.PAST_DUE,
        "Suspended": SubscriptionStatus.SUSPENDED,
        "Cancelled": SubscriptionStatus.CANCELLED,
        "Expired": SubscriptionStatus.EXPIRED,
    }

    BILLING_TO_FRAPPE = {
        BillingCycle.MONTHLY: "Monthly",
        BillingCycle.QUARTERLY: "Quarterly",
        BillingCycle.YEARLY: "Yearly",
    }

    BILLING_FROM_FRAPPE = {
        "Monthly": BillingCycle.MONTHLY,
        "Quarterly": BillingCycle.QUARTERLY,
        "Yearly": BillingCycle.YEARLY,
    }

    # =====================================================
    # Helpers
    # =====================================================

    @staticmethod
    def _naive(dt):
        """
        Convert timezone-aware datetimes to naive datetimes
        for MariaDB/Frappe.
        """
        if dt is None:
            return None

        if getattr(dt, "tzinfo", None):
            return dt.replace(tzinfo=None)

        return dt

    def _require_subscription_tenant(
        self,
        subscription: Subscription,
    ) -> str:

        tenant_id = self.current_tenant()

        if subscription.tenant_id != tenant_id:
            raise PermissionError(
                "Subscription belongs to a different tenant."
            )

        return tenant_id

    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        subscription: Subscription,
    ) -> Subscription:

        tenant_id = self._require_subscription_tenant(
            subscription
        )

        business = frappe.db.get_value(
            "Business Account",
            {
                "business_id": subscription.business_id,
            },
            [
                "tenant_id",
                "status",
            ],
            as_dict=True,
        )

        if not business:
            raise ValueError(
                f"Business Account '{subscription.business_id}' does not exist."
            )

        if business.tenant_id != tenant_id:
            raise PermissionError(
                "Business Account belongs to a different tenant."
            )

        if business.status != "Active":
            raise PermissionError(
                "Business Account must be Active."
            )

        existing_name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "subscription_id": subscription.subscription_id,
                "tenant_id": tenant_id,
            },
            "name",
        )

        if existing_name:
            doc = frappe.get_doc(
                self.DOCTYPE,
                existing_name,
            )
        else:
            doc = frappe.new_doc(
                self.DOCTYPE
            )

            doc.subscription_id = (
                subscription.subscription_id
            )
        doc.tenant_id = tenant_id
        doc.business_id = subscription.business_id
        doc.plan = subscription.plan.name

        doc.status = self.STATUS_TO_FRAPPE.get(
            subscription.status,
            "Trial",
        )

        doc.billing_cycle = self.BILLING_TO_FRAPPE.get(
            subscription.billing_cycle,
            "Monthly",
        )

        doc.start_date = self._naive(
            subscription.start_date
        )

        doc.renewal_date = self._naive(
            subscription.renewal_date
        )

        doc.trial_end = self._naive(
            subscription.trial_end
        )

        doc.cancelled_at = self._naive(
            subscription.cancelled_at
        )
	
        doc.grace_period_until = self._naive(
            subscription.grace_period_until
        )

        doc.auto_renew = subscription.auto_renew

        doc.terminated_on = self._naive(
            subscription.terminated_on
        )

        doc.termination_reason = (
            subscription.termination_reason
        )

        if existing_name:
            doc.save(
                ignore_permissions=True
            )
        else:
            doc.insert(
                ignore_permissions=True,
                ignore_links=True,
            )

        frappe.db.commit()

        return subscription

    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        subscription_id: str,
    ) -> Subscription | None:

        tenant_id = self.current_tenant()

        row = frappe.db.get_value(
            self.DOCTYPE,
            {
                "subscription_id": subscription_id,
                "tenant_id": tenant_id,
            },
            [
                "subscription_id",
                "tenant_id",
                "business_id",
                "plan",
                "status",
                "billing_cycle",
                "start_date",
                "renewal_date",
                "trial_end",
                "cancelled_at",
		"grace_period_until",
		"auto_renew",
		"terminated_on",
		"termination_reason",

            ],
            as_dict=True,
        )

        if not row:
            return None

        return self._row_to_model(row)

    # =====================================================
    # Get By Business
    # =====================================================


    def get_any_by_business(
        self,
        business_id: str,
    ):

        tenant_id = self.current_tenant()

        rows = frappe.db.get_all(
            self.DOCTYPE,
            filters={
                "business_id": business_id,
                "tenant_id": tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
            limit=1,
        )

        if not rows:
            return None

        row = frappe.db.get_value(
            self.DOCTYPE,
            rows[0].name,
            [
                "subscription_id",
                "tenant_id",
                "business_id",
                "plan",
                "status",
                "billing_cycle",
                "start_date",
                "renewal_date",
                "trial_end",
                "cancelled_at",
                "grace_period_until",
                "auto_renew",
                "terminated_on",
                "termination_reason",
            ],
            as_dict=True,
        )

        return self._row_to_model(row)


    def get_by_business(
        self,
        business_id: str,
    ) -> Subscription | None:

        tenant_id = self.current_tenant()
        business = frappe.db.get_value(
            "Business Account",
            {
                "business_id": business_id,
                "tenant_id": tenant_id,
            },
            [
                "status",
            ],
            as_dict=True,
        )

        if not business:
            raise ValueError(
                f"Business Account '{business_id}' "
                "does not exist in current tenant."
            )

        if business.status != "Active":
            raise PermissionError(
                "Business Account must be Active."
            )
        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "business_id": business_id,
                "tenant_id": tenant_id,
            },
            fields=[
                "subscription_id",
                "tenant_id",
                "business_id",
                "plan",
                "status",
                "billing_cycle",
                "start_date",
                "renewal_date",
                "trial_end",
                "cancelled_at",
                "grace_period_until",
                "auto_renew",
                "terminated_on",
                "termination_reason",
            ],
            order_by="creation desc",
        )

        if not rows:
            return None

        current_statuses = {
            "Active",
            "Past Due",
            "Trial",
        }

        candidates = [
            row
            for row in rows
            if row.status in current_statuses
        ]

        if len(candidates) > 1:
            raise RuntimeError(
                "Multiple current subscriptions found for "
                f"business '{business_id}' in tenant "
                f"'{tenant_id}'."
            )

        if not candidates:
            return None

        return self._row_to_model(
            candidates[0]
        )

    # =====================================================
    # All — Current Tenant Only
    # =====================================================

    def all(
        self,
    ) -> list[Subscription]:

        tenant_id = self.current_tenant()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "tenant_id": tenant_id,
            },
            fields=[
                "subscription_id",
                "tenant_id",
                "business_id",
                "plan",
                "status",
                "billing_cycle",
                "start_date",
                "renewal_date",
                "trial_end",
		"cancelled_at",
		"grace_period_until",
		"auto_renew",
		"terminated_on",
		"termination_reason",
            ],
            order_by="creation desc",
        )

        return [
            self._row_to_model(row)
            for row in rows
        ]

    # =====================================================
    # Exists
    # =====================================================

    def exists(
        self,
        subscription_id: str,
    ) -> bool:

        tenant_id = self.current_tenant()

        return bool(
            frappe.db.exists(
                self.DOCTYPE,
                {
                    "subscription_id": subscription_id,
                    "tenant_id": tenant_id,
                },
            )
        )

    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        subscription_id: str,
    ) -> None:

        tenant_id = self.current_tenant()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                "subscription_id": subscription_id,
                "tenant_id": tenant_id,
            },
            "name",
        )

        if not name:
            return

        frappe.delete_doc(
            self.DOCTYPE,
            name,
            force=True,
        )

        frappe.db.commit()

    # =====================================================
    # Clear — Current Tenant Only
    # =====================================================

    def clear(
        self,
    ) -> None:

        tenant_id = self.current_tenant()

        names = frappe.get_all(
            self.DOCTYPE,
            filters={
                "tenant_id": tenant_id,
            },
            pluck="name",
        )

        for name in names:
            frappe.delete_doc(
                self.DOCTYPE,
                name,
                force=True,
            )

        frappe.db.commit()

    # =====================================================
    # Model Conversion
    # =====================================================

    def _row_to_model(
        self,
        row,
    ) -> Subscription:

        plan_name = row.plan or "Unknown"

        plan = SubscriptionPlan(
            plan_id=plan_name.lower().replace(
                " ",
                "_",
            ),
            name=plan_name,
        )

        return Subscription(
            subscription_id=row.subscription_id,
            tenant_id=row.tenant_id,
            business_id=row.business_id,
            plan=plan,
            status=self.STATUS_FROM_FRAPPE.get(
                row.status,
                SubscriptionStatus.TRIAL,
            ),
            billing_cycle=self.BILLING_FROM_FRAPPE.get(
                row.billing_cycle,
                BillingCycle.MONTHLY,
            ),
            start_date=row.start_date,
            renewal_date=row.renewal_date,
            trial_end=row.trial_end,
            cancelled_at=row.cancelled_at,
            grace_period_until=row.grace_period_until,
            auto_renew=bool(row.auto_renew),
            terminated_on=row.terminated_on,
            termination_reason=row.termination_reason,
        )

    # =====================================================
    # Health
    # =====================================================

    def health(
        self,
    ) -> dict:

        tenant_id = self.current_tenant()

        return {
            "repository":
                "frappe_subscription_repository",

            "status":
                "healthy",

            "tenant":
                True,

            "tenant_id":
                tenant_id,

            "records":
                frappe.db.count(
                    self.DOCTYPE,
                    {
                        "tenant_id": tenant_id,
                    },
                ),
        }
