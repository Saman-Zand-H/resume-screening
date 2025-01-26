from graphql_auth.forms import PasswordLessRegisterForm as PasswordLessRegisterFormBase

from django import forms
from django.contrib.auth.forms import UserChangeForm as UserChangeFormBase
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _

from .fields import UsernameField
from .models import User


class UserChangeForm(UserChangeFormBase):
    class Meta(UserChangeFormBase.Meta):
        field_classes = {"username": UsernameField}


class PasswordLessRegisterForm(PasswordLessRegisterFormBase):
    def clean(self):
        self.cleaned_data["password1"] = self.cleaned_data["password2"] = make_password(None)
        return super().clean()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user


class OrganizationUserCreationForm(forms.Form):
    email = forms.EmailField(label=_("Email"))
    website = forms.URLField(label=_("Website"), assume_scheme="http")
    name = forms.CharField(label=_("Name"))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password_confirm = forms.CharField(label=_("Password Confirm"), widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["password_confirm"].widget.attrs.update({"autocomplete": "new-password"})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        email = cleaned_data.get("email")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", _("Passwords do not match"))

        if email and User.objects.filter(email=email).exists():
            self.add_error("email", _("Email already exists"))

        return cleaned_data
