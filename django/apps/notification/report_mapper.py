from functools import wraps
from typing import Dict, List

from django.db.models import Model
from django.utils.functional import classproperty

from .types import MapperKey, MapperReport, NotificationType, ReportMapperType


class ReportMapper:
    _registry: Dict[MapperKey, ReportMapperType] = {}

    @classmethod
    def register(cls, model: Model, notification_type: NotificationType):
        def decorator(func: ReportMapperType):
            key = MapperKey(model, notification_type)
            cls._registry[key] = func
            return wraps(func)

        return decorator

    @classmethod
    def get_mapper(cls, model: Model, notification_type: NotificationType) -> ReportMapperType:
        key = MapperKey(model, notification_type)
        return cls._registry.get(key)

    @classmethod
    def map(cls, instance: Model, notification_type: NotificationType) -> List[MapperReport]:
        return cls.get_mapper(instance._meta.model, notification_type)(instance)

    @classproperty
    def registry(cls):
        return cls._registry


register = ReportMapper.register
