from django.core import validators
from django.db import models
from django.utils.translation import gettext_lazy as _


class VertexAIModel(models.Model):
    slug = models.SlugField(
        verbose_name=_("Slug"),
        help_text=_("Slug for the model"),
        unique=True,
        db_index=True,
    )
    model_name = models.CharField(
        verbose_name=_("Model"),
        max_length=255,
    )
    instruction = models.TextField(
        verbose_name=_("Instruction"),
        help_text=_("Instructions for the model"),
        blank=True,
        null=True,
    )
    temperature = models.FloatField(
        verbose_name=_("Temperature"),
        help_text=_("Temperature for the model"),
        validators=[
            validators.MinValueValidator(0.0),
            validators.MaxValueValidator(1.0),
        ],
        default=1.0,
    )
    max_tokens = models.IntegerField(
        verbose_name=_("Max tokens"),
        help_text=_("Max tokens for the model"),
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(8192),
        ],
        default=8192,
    )

    def __str__(self):
        return self.slug

    class Meta:
        verbose_name = _("Vertex AI Model")
        verbose_name_plural = _("Vertex AI Models")
