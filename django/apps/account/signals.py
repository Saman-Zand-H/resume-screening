from common.models import Job, Skill

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .constants import VectorStores


@receiver([post_save, post_delete], sender=Job)
def jobs_clear_cache(*args, **kwargs):
    cache.delete(VectorStores.JOB.cache_key)


@receiver([post_save, post_delete], sender=Skill)
def skills_clear_cache(*args, **kwargs):
    instance = kwargs.get("instance")
    if instance and instance.insert_type == Skill.InsertType.AI:
        return
    cache.delete(VectorStores.SKILL.cache_key)
