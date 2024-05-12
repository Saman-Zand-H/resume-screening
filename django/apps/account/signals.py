from common.models import Job, Skill
from config.signals import job_available_triggered

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .constants import VectorStores
from .models import Profile, Referral, User
from .tasks import find_available_jobs


@receiver(post_save, sender=User)
def user_create_one_to_one_objetcs(sender, instance, created, **kwargs):
    if created:
        Referral.objects.create(user=instance)


@receiver([post_save, post_delete], sender=Job)
def jobs_clear_cache(*args, **kwargs):
    cache.delete(VectorStores.JOB.cache_key)


@receiver([post_save, post_delete], sender=Skill)
def skills_clear_cache(*args, **kwargs):
    instance = kwargs.get("instance")
    if instance and instance.insert_type == Skill.InsertType.AI:
        return
    cache.delete(VectorStores.SKILL.cache_key)


@receiver([job_available_triggered], sender=Profile)
def trigger_job_available(user: User, *args, **kwargs):
    find_available_jobs.delay(user_id=user.pk)
