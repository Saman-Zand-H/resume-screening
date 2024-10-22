from notification.context_mapper import ContextMapper, register

from django.utils.translation import gettext_lazy as _

from .constants import STAGE_ANNOTATIONS, ProfileAnnotationNames
from .models import Profile


@register(Profile)
class UserFirstName(ContextMapper):
    name = "first_name"
    help = _("User's first name")

    @classmethod
    def map(cls, instance: Profile):
        return instance.user.first_name


@register(Profile)
class UserLastName(ContextMapper):
    name = "last_name"
    help = _("User's last name")

    @classmethod
    def map(cls, instance: Profile):
        return instance.user.last_name


@register(Profile)
class UserEmail(ContextMapper):
    name = "email"
    help = _("User's email")

    @classmethod
    def map(cls, instance: Profile):
        return instance.user.email


@register(Profile)
class CompletedStages(ContextMapper):
    name = "completed_stages"
    help = _("A list of user's completed stages. The stage names are: %(stage_names)s") % {
        "stage_names": STAGE_ANNOTATIONS
    }

    @classmethod
    def map(cls, instance: Profile):
        return getattr(instance, ProfileAnnotationNames.COMPLETED_STAGES, [])


@register(Profile)
class IncompleteStages(ContextMapper):
    name = "incomplete_stages"
    help = _("A list of user's incomplete stages. The stage names are: %(stage_names)s") % {
        "stage_names": STAGE_ANNOTATIONS
    }

    @classmethod
    def map(cls, instance: Profile):
        return getattr(instance, ProfileAnnotationNames.INCOMPLETE_STAGES, [])
