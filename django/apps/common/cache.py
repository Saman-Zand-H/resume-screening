from typing import Tuple

from django.core.cache import cache
from django.db.models import QuerySet


class Cache:
    @staticmethod
    def get_or_set_qs(key: str, qs: QuerySet, timeout=None) -> Tuple[QuerySet, bool]:
        created = False
        if not (cache.get(key)):
            cache.set(key, qs, timeout)
            created = True
        return cache.get(key), created
