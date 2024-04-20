import contextlib
import re
from abc import abstractmethod
from inspect import signature
from typing import Any, Callable

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
            return cls(**kwargs)

        raise ValueError(f"Invalid kwargs for {cls.__name__}. Valid kwargs are {cls.get_instance_kwargs(cls.__init__)}")

    @abstractmethod
    def validate(self, value) -> None:
        """
        Raises a ValidationError if the value is invalid."""
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

    def validate(self, value):
        if not (self.min_value <= value <= self.max_value):
            raise ValidationError(_("Value is not in range"))
