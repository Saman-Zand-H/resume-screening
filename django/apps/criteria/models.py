import re
import uuid
from datetime import timedelta

from account.models import User
from common.models import FileModel, Job
from common.utils import fj
from common.validators import DOCUMENT_FILE_SIZE_VALIDATOR, IMAGE_FILE_SIZE_VALIDATOR, FileExtensionValidator
from computedfields.models import ComputedFieldsModel, computed
from markdownfield.models import MarkdownField
from markdownfield.validators import VALIDATOR_STANDARD
from model_utils.models import TimeStampedModel

from django.db import models
from django.db.models import Exists, OuterRef
from django.db.models.lookups import In
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .client.types import CombinedScore
from .client.types import Status as CriteriaStatus


def job_assessment_logo_path(instance, filename):
    return f"job_assessment/logo/{instance.id}/{filename}"


class JobAssessmentQuerySet(models.QuerySet):
    def filter_by_required(self, required, jobs):
        has_required_job_assessment = Exists(
            JobAssessmentJob.objects.filter(
                **{
                    fj(JobAssessmentJob.job_assessment): OuterRef(JobAssessment._meta.pk.attname),
                    fj(JobAssessmentJob.job, In.lookup_name): jobs,
                    fj(JobAssessmentJob.required): True,
                }
            ).values(JobAssessmentJob._meta.pk.attname)[:1]
        )
        if required:
            return self.filter(models.Q(**{fj(JobAssessment.required): True}) | has_required_job_assessment)
        return self.filter(models.Q(**{fj(JobAssessment.required): False}) & ~has_required_job_assessment)

    def related_to_user(self, user: User):
        return self.filter(
            models.Q(
                **{
                    fj(JobAssessmentResult.job_assessment.field.related_query_name(), JobAssessmentResult.user): user,
                    fj(
                        JobAssessmentResult.job_assessment.field.related_query_name(), JobAssessmentResult.status
                    ): JobAssessmentResult.Status.COMPLETED,
                }
            )
            | models.Q(
                **{
                    fj(JobAssessment.related_jobs, In.lookup_name): user.get_profile().interested_jobs.values_list(
                        "pk", flat=True
                    )
                }
            )
            | models.Q(**{fj(JobAssessment.required): True})
        ).distinct()


class JobAssessment(models.Model):
    related_jobs = models.ManyToManyField(
        Job, through="JobAssessmentJob", verbose_name=_("Related Jobs"), related_name="assessments"
    )
    package_id = models.CharField(max_length=64, verbose_name=_("Package ID"))
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
    retry_interval = models.DurationField(default=timedelta(weeks=1), verbose_name=_("Retry Interval"))
    count_limit = models.PositiveIntegerField(default=10, verbose_name=_("Count Limit"))
    time_limit = models.DurationField(default=timedelta(minutes=30), verbose_name=_("Time Limit"))
    required = models.BooleanField(default=False, verbose_name=_("Required"))

    objects = JobAssessmentQuerySet.as_manager()

    class Meta:
        verbose_name = _("Job Assessment")
        verbose_name_plural = _("Job Assessments")

    def __str__(self):
        return self.title

    def can_start(self, user) -> tuple[bool, str]:
        results = self.results.filter(**{fj(JobAssessmentResult.user): user})
        if results.exists():
            if results.count() >= self.count_limit:
                return False, _("You have reached the limit of assessments.")
            last_result = results.last()
            if last_result.status in (JobAssessmentResult.Status.COMPLETED, JobAssessmentResult.Status.TIMEOUT):
                if last_result.updated_at + self.retry_interval >= timezone.now():
                    return False, _("You can't start a new assessment yet.")
            else:
                return False, _("There is an incomplete assessment.")
        return True, None

    def is_required(self, jobs):
        return (
            JobAssessment.objects.filter(**{JobAssessment._meta.pk.attname: self.pk})
            .filter_by_required(True, jobs)
            .exists()
        )


class JobAssessmentJob(models.Model):
    job_assessment = models.ForeignKey(
        JobAssessment, on_delete=models.CASCADE, verbose_name=_("Job Assessment"), related_name="job_assessment_jobs"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name=_("Job"), related_name="job_assessment_jobs")
    required = models.BooleanField(default=False, verbose_name=_("Required"))

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
        GREAT = "great", _("Great")
        EXCEPTIONAL = "exceptional", _("Exceptional")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="job_assessment_results"
    )
    job_assessment = models.ForeignKey(
        JobAssessment, on_delete=models.CASCADE, verbose_name=_("Job Assessment"), related_name="results"
    )
    raw_status = models.CharField(max_length=64, verbose_name=_("Status"), default=CriteriaStatus.IN_PROGRESS.value)
    raw_score = models.JSONField(verbose_name=_("Raw Score"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    order_id = models.UUIDField(editable=False, default=uuid.uuid4, verbose_name=_("Order ID"))
    report_url = models.URLField(verbose_name=_("Report URL"), null=True, blank=True, editable=False)

    @computed(
        models.CharField(max_length=32, choices=UserScore.choices, null=True, blank=True),
        depends=[("self", ["raw_score"])],
    )
    def score(self):
        if self.raw_score is None:
            return
        score = CombinedScore.model_validate(self.raw_score).RankingScore
        if score:
            if score < 65:
                return self.UserScore.AVARAGE
            elif score < 75:
                return self.UserScore.GOOD
            elif score < 85:
                return self.UserScore.GREAT
            return self.UserScore.EXCEPTIONAL

    @computed(
        models.CharField(max_length=32, choices=Status.choices, null=True, blank=True, default=Status.NOT_STARTED),
        depends=[("self", ["raw_status"])],
    )
    def status(self):
        if self.is_timeout():
            return self.Status.TIMEOUT

        match = re.match(CriteriaStatus.EVALUATION_IN_PROGRESS.value, self.raw_status)
        if match or self.raw_status == CriteriaStatus.IN_PROGRESS.value:
            return self.Status.IN_PROGRESS
        elif self.raw_status == CriteriaStatus.SCHEDULED.value:
            return self.Status.NOT_STARTED
        elif self.raw_status == CriteriaStatus.COMPLETE.value:
            return self.Status.COMPLETED

    def is_timeout(self):
        if not self.created_at:
            return False
        return self.created_at + self.job_assessment.time_limit < timezone.now()

    class Meta:
        verbose_name = _("Job Assessment Result")
        verbose_name_plural = _("Job Assessment Results")

    def __str__(self):
        return f"{self.user.email} - {self.job_assessment.title} - {self.score}"


class JobAssessmentResultReportFile(TimeStampedModel, FileModel):
    SLUG = "job-assessment-result-report-file"

    job_assessment_result = models.OneToOneField(
        JobAssessmentResult,
        on_delete=models.CASCADE,
        related_name="report_file",
    )

    def get_validators(self):
        return [
            FileExtensionValidator(["pdf"]),
            DOCUMENT_FILE_SIZE_VALIDATOR,
        ]

    def get_upload_path(self, filename):
        return f"assessment/{self.job_assessment_result.id}/report_files/{filename}"

    def check_auth(self, request: HttpRequest = None):
        return request.user.is_authenticated and self.job_assessment_result.user == request.user

    class Meta:
        verbose_name = _("Job Assessmen Result Report File")
        verbose_name_plural = _("Job Assessmen Result Report Files")
