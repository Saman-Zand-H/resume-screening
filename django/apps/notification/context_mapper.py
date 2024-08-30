from collections import ChainMap
from functools import wraps
from operator import methodcaller
from typing import Dict, List

from django.db.models import Model

from .types import ReportMapperType


class ContextMapper:
    name: str
    help: str

    @classmethod
    def get_context(cls, instance: Model):
        return {cls.name: cls.map(instance)}

    @classmethod
    def map(cls, instance: Model):
        raise NotImplementedError("Method 'map' must be implemented")


class ContextMapperRegistry:
    _registry: Dict[Model, List[ContextMapper]] = {}

    @classmethod
    def register(cls, model: Model):
        def decorator(func: ReportMapperType):
            cls._registry.setdefault(model, []).append(func)
            return wraps(func)

        return decorator

    @classmethod
    def get_mapper(cls, model: Model) -> ReportMapperType:
        return cls._registry.get(model)

    @classmethod
    def registry(cls) -> Dict[Model, List[ContextMapper]]:
        return cls._registry

    @classmethod
    def get_context(cls, instance: Model):
        mappers = cls.get_mapper(instance._meta.model)
        if not mappers:
            return {}

        return {k: v for k, v in ChainMap(*map(methodcaller("get_context", instance=instance), mappers)).items()}


register = ContextMapperRegistry.register
