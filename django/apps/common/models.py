from cities_light.models import City

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import LANGUAGES


class Industry(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))

    class Meta:
        verbose_name = _("Industry")
        verbose_name_plural = _("Industries")

    def __str__(self):
        return self.title


class JobCategory(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, verbose_name=_("Industry"))

    class Meta:
        verbose_name = _("Job Category")
        verbose_name_plural = _("Job Categories")

    def __str__(self):
        return self.title


class Job(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, verbose_name=_("Category"))
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
    websites = ArrayField(models.URLField(), verbose_name=_("Websites"), blank=True, null=True)

    class Meta:
        verbose_name = _("University")
        verbose_name_plural = _("Universities")

    def __str__(self):
        return self.name


class SkillTopic(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, verbose_name=_("Industry"))

    class Meta:
        verbose_name = _("Skill Topic")
        verbose_name_plural = _("Skill Topics")

    def __str__(self):
        return self.title


class SkillQuerySet(models.QuerySet):
    def system(self):
        return self.filter(insert_type=Skill.InsertType.SYSTEM)

    def ai(self):
        return self.filter(insert_type=Skill.InsertType.AI)


class Skill(models.Model):
    class InsertType(models.TextChoices):
        SYSTEM = "system", _("System")
        AI = "ai", _("AI")

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    insert_type = models.CharField(
        max_length=10,
        choices=InsertType.choices,
        default=InsertType.SYSTEM,
        verbose_name=_("Insert Type"),
    )
    topic = models.ForeignKey(SkillTopic, on_delete=models.CASCADE, verbose_name=_("Topic"))
    objects = SkillQuerySet.as_manager()

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")

    def __str__(self):
        return self.title


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
    languages = ArrayField(models.CharField(choices=LANGUAGES, max_length=32), verbose_name=_("Languages"))

    class Meta:
        verbose_name = _("Language Proficiency Test")
        verbose_name_plural = _("Language Proficiency Tests")

    def __str__(self):
        return self.title
