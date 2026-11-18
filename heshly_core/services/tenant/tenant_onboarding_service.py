from __future__ import annotations

from datetime import UTC, datetime, timedelta
import re

import frappe

from heshly_core.models.business_account import BusinessAccount
from heshly_core.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    BillingCycle,
)
from heshly_core.models.user_business_membership import (
    UserBusinessMembership,
    MembershipRole,
)
from heshly_core.repositories.frappe_business_repository import (
    FrappeBusinessRepository,
)
from heshly_core.repositories.frappe_subscription_repository import (
    FrappeSubscriptionRepository,
)
from heshly_core.repositories.frappe_user_business_repository import (
    FrappeUserBusinessRepository,
)
from heshly_core.services.tenant.user_provisioning_service import (
    UserProvisioningService,
)
from heshly_core.services.tenant.tenant_id_strategy import (
    TenantIDStrategy,
)
from heshly_core.services.tenant.tenant_context import TenantContext


class TenantOnboardingService:
    """
    Creates a complete Heshly tenant during signup.

    Signup flow:

        Business Account
            ↓
        14-day Trial Subscription
            ↓
        Owner User
            ↓
        Owner Membership

    No custom customer domains are created.
    """

    TRIAL_DAYS = 14
    DEFAULT_PLAN = "Growth"

    def __init__(self):
        self.business_repo = FrappeBusinessRepository()
        self.subscription_repo = FrappeSubscriptionRepository()
        self.membership_repo = FrappeUserBusinessRepository()
        self.user_service = UserProvisioningService()
        self.context = TenantContext()

    @staticmethod
    def make_business_id(
        business_name: str,
        email: str,
    ) -> str:

        base = re.sub(
            r"[^a-z0-9]+",
            "_",
            business_name.strip().lower(),
        ).strip("_")

        if not base:
            base = "business"

        # Business ID is based on the business name only.
        # The owner's email must not become part of the tenant identity
        # or public Heshly subdomain.
        base = base[:70].strip("_")

        candidate = base
        counter = 2

        while frappe.db.exists(
            "Business Account",
            {"business_id": candidate},
        ):
            candidate = f"{base}_{counter}"
            counter += 1

        return candidate

    def onboard(
        self,
        business_name: str,
        owner_email: str,
        owner_password: str,
        phone: str | None = None,
        industry: str | None = None,
        location: str | None = None,
        plan_name: str = DEFAULT_PLAN,
    ):

        business_name = (business_name or "").strip()
        owner_email = (owner_email or "").strip().lower()
        owner_password = owner_password or ""

        if not business_name:
            raise ValueError(
                "Business name is required."
            )

        if not owner_email or "@" not in owner_email:
            raise ValueError(
                "A valid owner email is required."
            )

        if len(owner_password) < 8:
            raise ValueError(
                "Password must be at least 8 characters."
            )

        if frappe.db.exists(
            "User",
            owner_email,
        ):
            raise ValueError(
                "An account with this email already exists."
            )

        business_id = self.make_business_id(
            business_name,
            owner_email,
        )

        tenant_id = TenantIDStrategy.from_business_id(
            business_id,
        )

        self.context.set(tenant_id)

        now = datetime.now(UTC)
        trial_end = now + timedelta(
            days=self.TRIAL_DAYS
        )

        # Heshly-controlled tenant subdomain (server owns invariant).
        # Example: KIKL -> kikl.heshly.com, debug_test -> debug-test.heshly.com
        # This is not a custom domain. Normalize any non-alphanum to hyphen.
        _raw = business_id.strip().lower()
        _slug = re.sub(r"[^a-z0-9]+", "-", _raw).strip("-")
        domain = f"{_slug}.heshly.com"
        # Defensive: never allow shared portal domain
        if domain.lower() == "clients.heshly.com":
            raise ValueError("Generated domain collides with shared portal domain.")

        business_created = False
        subscription_created = False
        user_created = False
        membership_created = False

        try:
            # ---------------------------------------------
            # 1. Business Account
            # ---------------------------------------------

            business = BusinessAccount(
                business_id=business_id,
                tenant_id=tenant_id,
                name=business_name,
                domain=domain,
                email=owner_email,
                phone=phone,
            )

            if industry:
                business.profile.industry = industry

            if location:
                business.profile.location = location

            self.business_repo.save(business)
            business_created = True

            # ---------------------------------------------
            # 2. 14-Day Trial Subscription
            # ---------------------------------------------

            plan = SubscriptionPlan(
                plan_id=plan_name.lower().replace(
                    " ",
                    "_",
                ),
                name=plan_name,
            )

            subscription = Subscription(
                subscription_id=f"sub_{business_id}",
                tenant_id=tenant_id,
                business_id=business_id,
                plan=plan,
                status=SubscriptionStatus.TRIAL,
                billing_cycle=BillingCycle.MONTHLY,
                start_date=now,
                trial_end=trial_end,
                auto_renew=True,
            )

            self.subscription_repo.save(subscription)
            subscription_created = True

            # ---------------------------------------------
            # 3. Owner User
            # ---------------------------------------------

            owner_user = self.user_service.create_user(
                email=owner_email,
                first_name=business_name,
                password=owner_password,
            )

            user_created = True

            # ---------------------------------------------
            # 4. Owner Membership
            # ---------------------------------------------

            membership = UserBusinessMembership(
                membership_id=f"member_{business_id}",
                user=owner_user,
                tenant_id=tenant_id,
                business_id=business_id,
                role=MembershipRole.OWNER,
                active=True,
            )

            self.membership_repo.save(membership)
            membership_created = True

            frappe.db.commit()

            return {
                "success": True,
                "business": {
                    "business_id": business_id,
                    "tenant_id": tenant_id,
                    "business_name": business_name,
                    "email": owner_email,
                },
                "subscription": {
                    "subscription_id": (
                        subscription.subscription_id
                    ),
                    "plan": plan_name,
                    "status": "trial",
                    "billing_cycle": "monthly",
                    "trial_start": now.isoformat(),
                    "trial_end": trial_end.isoformat(),
                    "trial_days": self.TRIAL_DAYS,
                },
            }

        except Exception:
            frappe.db.rollback()

            # The repositories currently commit internally.
            # Therefore explicitly remove anything already
            # persisted by this signup attempt.

            try:
                # Membership first
                if membership_created:
                    names = frappe.get_all(
                        "User Business Membership",
                        filters={
                            "membership_id":
                                f"member_{business_id}",
                            "tenant_id":
                                tenant_id,
                        },
                        pluck="name",
                        ignore_permissions=True,
                    )

                    for name in names:
                        frappe.delete_doc(
                            "User Business Membership",
                            name,
                            force=True,
                        )

                # Subscription second
                if subscription_created:
                    names = frappe.get_all(
                        "Heshly Subscription",
                        filters={
                            "subscription_id":
                                f"sub_{business_id}",
                            "tenant_id":
                                tenant_id,
                        },
                        pluck="name",
                        ignore_permissions=True,
                    )

                    for name in names:
                        frappe.delete_doc(
                            "Heshly Subscription",
                            name,
                            force=True,
                        )

                # Business third
                if business_created:
                    names = frappe.get_all(
                        "Business Account",
                        filters={
                            "business_id":
                                business_id,
                            "tenant_id":
                                tenant_id,
                        },
                        pluck="name",
                        ignore_permissions=True,
                    )

                    for name in names:
                        frappe.delete_doc(
                            "Business Account",
                            name,
                            force=True,
                        )

                # User last
                if user_created and frappe.db.exists(
                    "User",
                    owner_email,
                    ignore_permissions=True,
                ):
                    frappe.delete_doc(
                        "User",
                        owner_email,
                        force=True,
                    )

                frappe.db.commit()

            except Exception:
                frappe.db.rollback()

            raise

        finally:
            self.context.clear()

    def health(self):
        return {
            "service": "tenant_onboarding_service",
            "status": "healthy",
        }
