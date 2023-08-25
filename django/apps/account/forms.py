from django.contrib.auth.forms import UserChangeForm as UserChangeFormBase

from .fields import UsernameField


class UserChangeForm(UserChangeFormBase):
    class Meta(UserChangeFormBase.Meta):
        field_classes = {"username": UsernameField}
