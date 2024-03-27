from enum import StrEnum
from typing import List

from .app_settings import app_settings


def are_subscriptions_valid(subscriptions: List[StrEnum]):
    return any(i.value in app_settings.SUBSCRIPTIONS for i in subscriptions)


def get_all_subclasses(klass):
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses
