from django.db import models
from django.utils.translation import gettext_lazy as _


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
