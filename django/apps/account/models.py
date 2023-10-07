from colorfield.fields import ColorField
from common.models import Job, University
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
    return f"profile/{instance.user.id}/full_body_image/{filename}"


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
    job = models.ManyToManyField(Job, verbose_name=_("Job"), blank=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return self.user.email


class Field(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Field"))

    class Meta:
        verbose_name = _("Field")
        verbose_name_plural = _("Fields")

    def __str__(self):
        return self.name


class Education(models.Model):
    class DegreeChoices(models.TextChoices):
        BACHELORS = "Bachelors", _("Bachelors")
        MASTERS = "Masters", _("Masters")
        PHD = "PhD", _("PhD")
        ASSOCIATE = "Associate", _("Associate")
        DIPLOMA = "Diploma", _("Diploma")
        CERTIFICATE = "Certificate", _("Certificate")

    class StatusChoices(models.TextChoices):
        VERIFIED = "Verified", _("Verified")
        REJECTED = "Rejected", _("Rejected")
        PENDING = "Pending", _("Pending")
        DRAFT = "Draft", _("Draft")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    field = models.ForeignKey(Field, on_delete=models.CASCADE, verbose_name=_("Field"))
    degree = models.CharField(max_length=50, choices=DegreeChoices.choices, verbose_name=_("Degree"))
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name=_("University"))
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=StatusChoices.choices,
        verbose_name=_("Status"),
        default=StatusChoices.PENDING,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Education")
        verbose_name_plural = _("Educations")

    def __str__(self):
        return f"{self.user.email} - {self.degree} in {self.field.name}"
