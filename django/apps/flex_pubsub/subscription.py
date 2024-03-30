from enum import Enum
from itertools import chain
from operator import attrgetter
from typing import List, Type

from .app_settings import app_settings
from .utils import get_all_subclasses


class SubscriptionBase(Enum):
    @classmethod
    def get_all_subscriptions(cls) -> List[Type["SubscriptionBase"]]:
        subscriptions = get_all_subclasses(cls)

        if len(subscriptions) != len(set(subscription for subscription in subscriptions)):
            raise ValueError("Subscriptions should have unique values.")

        return list(subscriptions)

    @classmethod
    def validate_chosen_subscriptions(cls):
        selected_subscriptions = app_settings.SUBSCRIPTIONS
        all_subscriptions = map(attrgetter("value"), chain.from_iterable(cls.get_all_subscriptions()))
        invalid_subscriptions = list(
            filter(
                lambda subscription: subscription not in all_subscriptions,
                selected_subscriptions,
            )
        )
        if invalid_subscriptions and selected_subscriptions:
            raise ValueError(f"Invalid subscriptions: {', '.join(map(str, invalid_subscriptions))}")
