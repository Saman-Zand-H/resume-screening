from account.models import User
from common.models import Industry

from django.db import models
from django.utils.translation import gettext_lazy as _


def get_logo_upload_path(instance, filename):
    return f"courses/{instance.id}/logo/{filename}"


class Course(models.Model):
    class Type(models.TextChoices):
        GENERAL = "general", _("General")
        OTHER = "other", _("Other")

    name = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.ImageField(upload_to=get_logo_upload_path, blank=True, null=True)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.GENERAL)
    industries = models.ManyToManyField(Industry)


class CourseResult(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="course_results")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.NOT_STARTED)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
