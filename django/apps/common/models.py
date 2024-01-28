from cities_light.models import City
from mptt.models import MPTTModel, TreeForeignKey

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


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
    require_appearance_data = models.BooleanField(default=False, verbose_name=_("Require Appearance Data"))

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


class SkillQuerySet(models.QuerySet):
    def system(self):
        return self.filter(insert_type=Skill.InsertType.SYSTEM)

    def ai(self):
        return self.filter(insert_type=Skill.InsertType.AI)


class Skill(MPTTModel):
    class InsertType(models.TextChoices):
        SYSTEM = "system", _("System")
        AI = "ai", _("AI")

    title = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Title"),
    )
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name=_("Job"), null=True, blank=True)
    insert_type = models.CharField(
        max_length=10,
        choices=InsertType.choices,
        default=InsertType.SYSTEM,
        verbose_name=_("Insert Type"),
    )
    objects = SkillQuerySet.as_manager()

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
