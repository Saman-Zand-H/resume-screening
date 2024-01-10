from cities_light.models import City
from mptt.models import MPTTModel, TreeForeignKey
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.validators import VALIDATOR_STANDARD

from django.db import models
from django.utils.translation import gettext_lazy as _

from django.core.exceptions import ValidationError

from common.validators import IMAGE_FILE_SIZE_VALIDATOR


def job_assessment_logo_path(instance, filename):
    return f"job_assessment/logo/{instance.user.id}/{filename}"


class Language(models.Model):
    name = models.CharField(_("Language Name"), max_length=50, unique=True)
    code = models.CharField(_("Language Code"), max_length=5, unique=True)

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobCategory(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))

    class Meta:
        verbose_name = _("Job Category")
        verbose_name_plural = _("Job Categories")

    def __str__(self):
        return self.title


class JobIndustry(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))

    class Meta:
        verbose_name = _("Job Industry")
        verbose_name_plural = _("Job Industries")

    def __str__(self):
        return self.title


class Job(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, verbose_name=_("Category"))
    industry = models.ForeignKey(JobIndustry, on_delete=models.CASCADE, verbose_name=_("Industry"))

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")

    def __str__(self):
        return self.title


class Field(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Field"))

    class Meta:
        verbose_name = _("Field")
        verbose_name_plural = _("Fields")

    def __str__(self):
        return self.name


class University(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name=_("City"))
    website = models.URLField(verbose_name=_("Website"))

    class Meta:
        verbose_name = _("University")
        verbose_name_plural = _("Universities")

    def __str__(self):
        return self.name


class Skill(MPTTModel):
    title = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Title"),
    )
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name=_("Job"), null=True, blank=True)

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")

    def __str__(self):
        return self.title

    def clean(self):
        if self.job and self.parent is not None:
            raise ValidationError({"job": _("Only level one skills can have jobs")})


class Position(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))

    class Meta:
        verbose_name = _("Position")
        verbose_name_plural = _("Positions")

    def __str__(self):
        return self.title


class LanguageProficiencyTest(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"), unique=True)
    min_score = models.FloatField(verbose_name=_("Minimum Score"))
    max_score = models.FloatField(verbose_name=_("Maximum Score"))
    overall_min_score = models.FloatField(verbose_name=_("Overall Minimum Score"))
    overall_max_score = models.FloatField(verbose_name=_("Overall Maximum Score"))

    class Meta:
        verbose_name = _("Language Proficiency Test")
        verbose_name_plural = _("Language Proficiency Tests")

    def __str__(self):
        return self.title


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
