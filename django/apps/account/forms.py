from graphql_auth.forms import PasswordLessRegisterForm as PasswordLessRegisterFormBase

from django.contrib.auth.forms import UserChangeForm as UserChangeFormBase
from django.contrib.auth.hashers import make_password

from .fields import UsernameField


class UserChangeForm(UserChangeFormBase):
    class Meta(UserChangeFormBase.Meta):
        field_classes = {"username": UsernameField}


class PasswordLessRegisterForm(PasswordLessRegisterFormBase):
    def clean(self):
        self.cleaned_data["password1"] = self.cleaned_data["password2"] = make_password(None)
        return super().clean()
