from typing import List, Type

from .app_settings import app_settings
from .utils import get_all_subclasses


class SubscriptionBase:
    @classmethod
    def get_all_subscription(cls) -> List[Type["SubscriptionBase"]]:
        subscriptions = get_all_subclasses(cls)
        members = set()

        for subscription in subscriptions:
            for member in subscription:
                if member in members:
                    raise ValueError(f"Member {member} is already in a subscription")
                members.add(member)

        return subscriptions

    @classmethod
    def validate_chosen_subscriptions(cls):
        selected_subscriptions = app_settings.SUBSCRIPTIONS
        all_subscriptions = cls.get_all_subscription()
        invalid_subscriptions = filter(
            lambda subscription: subscription not in all_subscriptions, selected_subscriptions
        )

        if invalid_subscriptions and selected_subscriptions:
            raise ValueError(f"Invalid subscriptions: {', '.join(map(str, invalid_subscriptions))}")
