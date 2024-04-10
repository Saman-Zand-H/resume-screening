from common.cache import Cache

from django.db import models

from .constants import CONTEXT_ALL_CACHE_KEY


class CVContextManager(models.Manager):
    class CVContextQueryset(models.QuerySet):
        def all(self):
            return Cache.get_or_set_qs(CONTEXT_ALL_CACHE_KEY, super().all())[0]

    def get_queryset(self):
        return self.CVContextQueryset(self.model, using=self._db)

    def all(self):
        return self.get_queryset().all()
