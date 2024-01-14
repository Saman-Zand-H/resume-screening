from django.db import models
from django.utils.translation import gettext_lazy as _

from computedfields.models import ComputedFieldsModel, computed
from markdownfield.models import MarkdownField
from markdownfield.validators import VALIDATOR_STANDARD

from common.models import Job
from common.validators import IMAGE_FILE_SIZE_VALIDATOR
from account.models import User


def job_assessment_logo_path(instance, filename):
    return f"job_assessment/logo/{instance.user.id}/{filename}"


class JobAssessment(models.Model):
    related_jobs = models.ManyToManyField(
        Job, through="JobAssessmentJob", verbose_name=_("Related Jobs"), related_name="assessments"
    )
    service_id = models.CharField(max_length=64, verbose_name=_("Service ID"))
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    logo = models.ImageField(
        upload_to=job_assessment_logo_path,
        validators=[IMAGE_FILE_SIZE_VALIDATOR],
        null=True,
        blank=True,
        verbose_name=_("Logo"),
    )
    short_description = models.CharField(max_length=255, verbose_name=_("Short Description"))
    description = MarkdownField(rendered_field="description_rendered", validator=VALIDATOR_STANDARD)
    resumable = models.BooleanField(default=False, verbose_name=_("Resumable"))

    class Meta:
        verbose_name = _("Job Assessment")
        verbose_name_plural = _("Job Assessments")

    def __str__(self):
        return self.title


class JobAssessmentJob(models.Model):
    job_assessment = models.ForeignKey(
        JobAssessment, on_delete=models.CASCADE, verbose_name=_("Job Assessment"), related_name="job_assessment_jobs"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name=_("Job"), related_name="job_assessment_jobs")
    required = models.BooleanField(default=False, verbose_name=_("Required"))
    retry_interval = models.DurationField(null=True, blank=True, verbose_name=_("Retry Interval"))

    class Meta:
        verbose_name = _("Job Assessment Job")
        verbose_name_plural = _("Job Assessment Jobs")
        unique_together = ("job_assessment", "job")

    def __str__(self):
        return f"{self.job_assessment.title} - {self.job.title}"


class JobAssessmentResult(ComputedFieldsModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")
        TIMEOUT = "timeout", _("Timeout")

    class UserScore(models.TextChoices):
        AVARAGE = "average", _("Average")
        GOOD = "good", _("Good")
        GREAT = "greate", _("Great")
        EXCEPTIONAL = "exceptional", _("Exceptional")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="job_assessment_results"
    )
    job_assessment = models.ForeignKey(
        JobAssessment, on_delete=models.CASCADE, verbose_name=_("Job Assessment"), related_name="results"
    )
    status = models.CharField(
        max_length=64, choices=Status.choices, verbose_name=_("Status"), default=Status.NOT_STARTED
    )
    raw_score = models.JSONField(verbose_name=_("Raw Score"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    @computed(
        models.CharField(max_length=32, choices=UserScore.choices, null=True, blank=True),
        depends=[("self", ["raw_score"])],
    )
    def score(self):
        score = self.raw_score.get("score")
        if score:
            if score < 65:
                return self.UserScore.AVARAGE
            elif score < 75:
                return self.UserScore.GOOD
            elif score < 85:
                return self.UserScore.GREAT
            return self.UserScore.EXCEPTIONAL

    class Meta:
        verbose_name = _("Job Assessment Result")
        verbose_name_plural = _("Job Assessment Results")

    def __str__(self):
        return f"{self.user.email} - {self.job_assessment.title} - {self.score}"
