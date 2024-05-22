from account.models import User
from common.models import Industry

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .client.client import academy_client
from .client.exceptions import (
    AcademyBadRequestException,
    AcademyNotFoundException,
)
from .client.types import (
    EnrollUserInCourseRequest,
    GenerateLoginUrlRequest,
    GetCourseUrlByIdRequest,
    GetOrCreateUserRequest,
)


def get_logo_upload_path(instance, filename):
    return f"courses/{instance.id}/logo/{filename}"


class CourseQuerySet(models.QuerySet):
    def related_to_user(self, user):
        q = Q(is_required=True) | Q(results__user=user, results__status=CourseResult.Status.COMPLETED)
        if profile := user.get_profile():
            q |= Q(
                industries__in=Industry.objects.filter(jobcategory__job__in=profile.interested_jobs.all())
                .distinct()
                .values_list("id", flat=True)
            )
        return self.filter(q).distinct()


class Course(models.Model):
    class Type(models.TextChoices):
        GENERAL = "general", _("General")
        OTHER = "other", _("Other")

    name = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.ImageField(upload_to=get_logo_upload_path, blank=True, null=True)
    external_id = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.GENERAL)
    industries = models.ManyToManyField(Industry)
    is_required = models.BooleanField(default=False)
    objects = CourseQuerySet.as_manager()

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")

    def __str__(self):
        return self.name


class CourseResult(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="results")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="course_results")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.NOT_STARTED.value)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Course Result")
        verbose_name_plural = _("Course Results")
        unique_together = ("course", "user")

    def __str__(self):
        return f"{self.user} - {self.course}"

    def get_login_url(self):
        course_id = self.course.external_id
        try:
            redirect_url = academy_client.get_coures_url_by_id(GetCourseUrlByIdRequest(course_id=course_id)).url
        except AcademyNotFoundException:
            raise ValidationError(_("Course not found"))
        try:
            wp_user_id = academy_client.get_or_create_user(
                GetOrCreateUserRequest(
                    external_id=str(self.user.pk),
                    email=self.user.email,
                    first_name=self.user.first_name,
                    last_name=self.user.last_name,
                )
            ).user_id
        except AcademyBadRequestException:
            raise ValidationError(_("User already exists in the academy"))

        academy_client.enroll_user_in_course(EnrollUserInCourseRequest(user_id=wp_user_id, course_id=course_id))

        return academy_client.generate_login_url(
            GenerateLoginUrlRequest(user_id=wp_user_id, redirect_uri=redirect_url)
        ).login_url
