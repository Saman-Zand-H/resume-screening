from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from .eav_validator import ValidatorRegistry
from .utils import validate_field_exists


class EavAttribute(models.Model):
    validators = ArrayField(
        models.CharField(max_length=255, choices=ValidatorRegistry.get_choices()),
        default=list,
        verbose_name=_("Validators"),
    )
    validator_kwargs = models.JSONField(
        default=dict,
        help_text=_("A list of kwargs dictionaries"),
        verbose_name=_("Validator kwargs"),
    )

    def __str__(self):
        return self.title

    def get_validator_instances(self):
        try:
            validator_instances = [
                ValidatorRegistry.get_validator(validator_slug).initialize_from_kwargs(**self.validator_kwargs)
                for validator_slug in self.validators
                if ValidatorRegistry.get_validator(validator_slug)
            ]
        except ValidationError as e:
            raise ValidationError({EavAttribute.validator_kwargs.field.name: next(iter(e.messages))}) from e

        if len(validator_instances) != len(self.validators):
            missing_validators = set(self.validators) - {v.slug for v in validator_instances}
            raise ValueError(f"Validators {', '.join(missing_validators)} do not exist")

        return validator_instances

    class Meta:
        abstract = True
        verbose_name = _("Eav Attribute")
        verbose_name_plural = _("Eav Attributes")

    def clean(self):
        self.get_validator_instances()


class EavValue(models.Model):
    attribute_field_name = "attribute"
    value = models.CharField(max_length=255, verbose_name=_("Value"))

    def clean(self):
        attribute = getattr(self, self.attribute_field_name, None)
        if not attribute:
            raise ValueError("Attribute is required to be implemented.")

        for validator in attribute.get_validator_instances():
            validator.validate(self.value)

    @classmethod
    def validate_fields(cls):
        validate_field_exists(cls, cls.attribute_field_name)

    class Meta:
        abstract = True
        verbose_name = _("Eav Value")
        verbose_name_plural = _("Eav Values")
