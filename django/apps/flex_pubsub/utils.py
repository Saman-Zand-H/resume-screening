from typing import List

from .app_settings import app_settings


def are_subscriptions_valid(subscriptions: List[str]):
    return set(subscriptions).intersection(app_settings.SUBSCRIPTIONS)


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
