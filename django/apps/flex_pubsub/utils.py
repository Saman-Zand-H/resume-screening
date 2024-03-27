from typing import List

from .app_settings import app_settings


def are_categories_valid(categories: List[str]):
    return set(categories).intersection(app_settings.CATEGORIES)


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
