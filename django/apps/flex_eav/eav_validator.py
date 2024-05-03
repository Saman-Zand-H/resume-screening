import contextlib
import re
from abc import abstractmethod
from inspect import signature
from typing import Any, Callable, List

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ValidatorBase:
    title: str
    slug: str

    @staticmethod
    def get_instance_kwargs(callable: Callable, **kwargs):
        return set(signature(callable).parameters)

    @classmethod
    def initialize_from_kwargs(cls, **kwargs):
        with contextlib.suppress(KeyError, AttributeError, ValueError):
            cls.validate_kwargs(cls, **(instance_kwargs := kwargs.get(cls.slug)))
            return cls(**instance_kwargs)

        raise ValueError(f"Invalid kwargs for {cls.__name__}. Valid kwargs are {cls.get_instance_kwargs(cls.__init__)}")

    @abstractmethod
    def validate(self, value) -> None:
        """
        Raises a ValidationError if the value is invalid."""
        pass

    @abstractmethod
    def validate_kwargs(self, **kwargs):
        """
        Raises a ValidationError if the kwargs are invalid"""
        pass

    @abstractmethod
    def __init__(self, **validator_kwargs: dict[str, Any]):
        pass


class ValidatorRegistry:
    title: str
    slug: str
    validators = {}

    @classmethod
    def register(cls, validator):
        cls.validators[validator.slug] = validator

    @classmethod
    def get_validator(cls, slug):
        return cls.validators.get(slug)

    @classmethod
    def get_choices(cls):
        return [(slug, validator.title) for slug, validator in cls.validators.items()]


register = ValidatorRegistry.register


@register
class RegexValidator(ValidatorBase):
    title = _("Regex")
    slug = "regex"

    def __init__(self, pattern: str):
        self.pattern = pattern

    def validate_kwargs(self, **kwargs):
        if not ((pattern := kwargs.get("pattern")) and isinstance(pattern, str)):
            raise ValidationError(_("Pattern is required"))

    def validate(self, value):
        if not re.match(self.pattern, value):
            raise ValidationError(_("Value does not match regex"))


@register
class RangeValidator(ValidatorBase):
    title = _("Range")
    slug = "range"

    def __init__(self, min_value: int, max_value: int):
        self.min_value = min_value
        self.max_value = max_value

    def validate_kwargs(self, **kwargs):
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")

        if not all((v is not None for v in (min_value, max_value))):
            raise ValidationError(_("min_value and max_value are required"))

        if not all(map(lambda x: str(x).isdigit, (min_value, max_value))):
            raise ValidationError(_("min_value and max_value must be integers"))

    def validate(self, value):
        try:
            if not (self.min_value <= float(value) <= self.max_value):
                raise ValidationError(_("Value is not in range: %s - %s") % (self.min_value, self.max_value))
        except ValueError:
            raise ValidationError(_("Value must be an integer"))


@register
class ChoiceValidator(ValidatorBase):
    title = _("Choice")
    slug = "choice"

    def __init__(self, choices: List[str]):
        self.choices = choices

    def validate_kwargs(self, **kwargs):
        if not (choices := kwargs.get("choices")):
            raise ValidationError(_("Choices are required"))

        if not isinstance(choices, list):
            raise ValidationError(_("Choices must be a list"))

    def validate(self, value: str):
        if value.lower() not in map(str.lower, self.choices):
            raise ValidationError({_("Value is not in choices. Valid choices are: %s") % ", ".join(self.choices)})
