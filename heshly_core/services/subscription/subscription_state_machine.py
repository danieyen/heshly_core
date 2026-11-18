from heshly_core.models.subscription import SubscriptionStatus


class SubscriptionStateMachine:

    ALLOWED = {

        SubscriptionStatus.TRIAL: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELLED,
        },

        SubscriptionStatus.ACTIVE: {
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
        },

        SubscriptionStatus.PAST_DUE: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
        },

        SubscriptionStatus.CANCELLED: {
            SubscriptionStatus.EXPIRED,
        },

        SubscriptionStatus.EXPIRED: set(),
    }


    @classmethod
    def can_transition(
        cls,
        current,
        target,
    ):
        return target in cls.ALLOWED.get(
            current,
            set(),
        )


    @classmethod
    def validate(
        cls,
        current,
        target,
    ):
        if not cls.can_transition(
            current,
            target,
        ):
            raise ValueError(
                f"Invalid subscription transition: "
                f"{current.value} -> {target.value}"
            )
