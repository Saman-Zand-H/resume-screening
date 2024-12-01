from common.models import Job, Skill
from common.utils import fj
from flex_observer.types import FieldsObserverRegistry

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .constants import JOB_AVAILABLE_MIN_PERCENT_TRIGGER_THRESHOLD, VectorStores
from .models import Contactable, Organization, Profile, Referral, SupportTicket, User
from .tasks import find_available_jobs, user_task_runner


@receiver(post_save, sender=SupportTicket)
def support_ticket_notification(instance, **kwargs):
    instance.notify()


@receiver(post_save, sender=User)
def user_create_one_to_one_objetcs(sender, instance, created, **kwargs):
    if created:
        Referral.objects.create(**{fj(Referral.user): instance})
        Profile.objects.create(**{fj(Profile.user): instance})


@receiver(pre_save, sender=Profile)
def run_find_available_jobs(instance, **kwargs):
    old_instance = Profile.objects.filter(**{Profile._meta.pk.attname: instance.pk}).first()
    if (
        old_instance
        and old_instance.score != instance.score
        and instance.completion_percentage >= JOB_AVAILABLE_MIN_PERCENT_TRIGGER_THRESHOLD
    ):
        user_task_runner(find_available_jobs, user_id=instance.user.pk, task_user_id=instance.user.pk)


@receiver(post_save, sender=Profile)
@receiver(post_save, sender=Organization)
def create_contactable(sender, instance, created, **kwargs):
    if created:
        instance.contactable = Contactable.objects.create()
        instance.save()


@receiver(post_delete, sender=Profile)
@receiver(post_delete, sender=Organization)
def delete_contactable(sender, instance, **kwargs):
    instance.contactable.delete()


@receiver([post_save, post_delete], sender=Job)
def jobs_clear_cache(*args, **kwargs):
    cache.delete(VectorStores.JOB.cache_key)


@receiver([post_save, post_delete], sender=Skill)
def skills_clear_cache(*args, **kwargs):
    instance = kwargs.get("instance")
    if instance and instance.insert_type == Skill.InsertType.AI:
        return
    cache.delete(VectorStores.SKILL.cache_key)


FieldsObserverRegistry.register_all()
