from notification.context_mapper import ContextMapper, register

from django.utils.translation import gettext_lazy as _

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
