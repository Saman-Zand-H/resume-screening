from colorfield.fields import ColorField
from common.validators import ValidateFileSize

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


User._meta.get_field("email")._unique = True
User._meta.get_field("email").blank = False
User._meta.get_field("email").null = False
User._meta.get_field("username").blank = True
User._meta.get_field("username").null = True


def full_body_image_path(instance, filename):
    return f"full_body_images/{instance.user.id}/{filename}"


class UserProfile(models.Model):
    class SkinColor(models.TextChoices):
        VERY_FAIR = "#FFDFC4", "Very Fair"
        FAIR = "#F0D5B1", "Fair"
        LIGHT = "#E5B897", "Light"
        LIGHT_MEDIUM = "#D9A377", "Light Medium"
        MEDIUM = "#C68642", "Medium"
        OLIVE = "#A86B33", "Olive"
        BROWN = "#8D5524", "Brown"
        DARK_BROWN = "#603913", "Dark Brown"
        VERY_DARK = "#3B260B", "Very Dark"
        DEEP = "#100C08", "Deep"

    class EyeColor(models.TextChoices):
        AMBER = "#FFBF00", "Amber"
        BLUE = "#5DADEC", "Blue"
        BROWN = "#6B4226", "Brown"
        GRAY = "#BEBEBE", "Gray"
        GREEN = "#1CAC78", "Green"
        HAZEL = "#8E7618", "Hazel"
        RED = "#FF4500", "Red"
        VIOLET = "#8F00FF", "Violet"

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    height = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    skin_color = ColorField(choices=SkinColor.choices, null=True, blank=True, verbose_name=_("Skin Color"))
    hair_color = ColorField(null=True, blank=True, verbose_name=_("Hair Color"))
    eye_color = ColorField(choices=EyeColor.choices, null=True, blank=True, verbose_name=_("Eye Color"))
    full_body_image = models.ImageField(
        upload_to=full_body_image_path,
        validators=[ValidateFileSize(5)],
        null=True,
        blank=True,
        verbose_name=_("Full Body Image"),
    )

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return self.user.email
