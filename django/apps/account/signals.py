from common.models import Job, Skill
from flex_observer.types import FieldsObserverRegistry

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .constants import VectorStores
from .models import Referral, SupportTicket, User


@receiver(post_save, sender=SupportTicket)
def support_ticket_notification(instance, **kwargs):
    instance.notify()


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


# @receiver(pre_save, sender=Profile)
# def check_score_threshold(instance: Profile, sender: Type[Profile], *args, **kwargs):
#     old_score = sender.objects.get(pk=instance.pk).score if instance.pk else None
#     if not instance.scores or old_score == instance.score or instance.score < JOB_AVAILABLE_MIN_SCORE_TRIGGER_THRESHOLD:
#         return

#     user_task_runner(find_available_jobs, user_id=instance.user.pk, task_user_id=instance.user.pk)


# @receiver(post_save, sender=Profile)
# def initialize_scores(instance: Profile, sender: Type[Profile], created, *args, **kwargs):
#     if not created and instance.scores:
#         return

#     instance.scores = UserScorePack.calculate(instance.user)
#     instance.score = sum(instance.scores.values())
#     instance.save()

FieldsObserverRegistry.register_all()
