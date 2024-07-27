from typing import Optional

from flex_blob.models import FileModel as BaseFileModel
from flex_eav.models import EavAttribute

from django.contrib.postgres.fields import ArrayField
from django.core import checks
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import LANGUAGES


class SlugTitleAbstract(models.Model):
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_("Slug"),
    )
    title = models.CharField(verbose_name=_("Title"), max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.slug}: {self.title}"


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
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
        ordering = ("title",)

    def __str__(self):
        return self.title


class Field(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))

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
    topic = models.ForeignKey(SkillTopic, on_delete=models.CASCADE, verbose_name=_("Topic"), null=True, blank=True)
    objects = SkillQuerySet.as_manager()

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")

    def __str__(self):
        return self.title


class LanguageProficiencyTest(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"), unique=True)
    languages = ArrayField(models.CharField(choices=LANGUAGES, max_length=32), verbose_name=_("Languages"))

    class Meta:
        verbose_name = _("Language Proficiency Test")
        verbose_name_plural = _("Language Proficiency Tests")

    def __str__(self):
        return self.title


class LanguageProficiencySkill(EavAttribute):
    slug = models.SlugField(max_length=255, verbose_name=_("Slug"), unique=True)
    test = models.ForeignKey(
        LanguageProficiencyTest,
        on_delete=models.CASCADE,
        verbose_name=_("Language Proficiency Test"),
        related_name="skills",
    )
    skill_name = models.CharField(max_length=255, verbose_name=_("Skill Name"))

    def __str__(self):
        return self.slug

    class Meta:
        verbose_name = _("Language Proficiency Skill")
        verbose_name_plural = _("Language Proficiency Skills")


class FileModel(BaseFileModel):
    SLUG = None

    class Meta:
        abstract = True

    @classmethod
    def check(cls, **kwargs):
        from .utils import get_file_models

        errors = super().check(**kwargs)
        if not cls.SLUG:
            errors.append(checks.Error("SLUG must be set", obj=cls))
        else:
            for model in get_file_models():
                if cls is model:
                    continue
                if cls.SLUG == model.SLUG:
                    errors.append(
                        checks.Error(
                            f"SLUG '{cls.SLUG}' is already used in {model._meta.label}",
                            obj=cls,
                        )
                    )
        return errors

    @classmethod
    def get_related_fields(cls):
        return [field for field in cls._meta.get_fields() if isinstance(field, models.ForeignObjectRel)]

    @classmethod
    def get_user_temporary_file(cls, *args, **kwargs) -> Optional["FileModel"]:
        return None

    @classmethod
    def is_used(cls, *args, **kwargs) -> bool:
        return cls.objects.exclude(
            **{field.field.related_query_name(): None for field in cls.get_related_fields()}
        ).exists()


class JobBenefit(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Job Benefit")
        verbose_name_plural = _("Job Benefits")

    def __str__(self):
        return self.name
