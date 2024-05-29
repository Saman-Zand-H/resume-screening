from common.models import Job, Skill
from flex_observer.types import FieldsObserverRegistry

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .constants import VectorStores
from .models import Contactable, Organization, Profile, Referral, SupportTicket, User


@receiver(post_save, sender=SupportTicket)
def support_ticket_notification(instance, **kwargs):
    instance.notify()


@receiver(post_save, sender=User)
def user_create_one_to_one_objetcs(sender, instance, created, **kwargs):
    if created:
        Referral.objects.create(user=instance)
        Profile.objects.create(user=instance)


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
