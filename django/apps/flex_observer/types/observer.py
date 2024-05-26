from typing import Callable, ClassVar, Generic, List, Literal, Type, TypeVar

from pydantic import BaseModel, Field, PrivateAttr

from django.db.models import Model
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save

M2mChangedActions = Literal["pre_add", "post_add", "pre_remove", "post_remove", "pre_clear", "post_clear"]
InstanceType = TypeVar("InstanceType", bound=Model)
FLEX_OBSERVER_CONTEXT_NAME = "_fo_context"


class FieldsObserverRegistry:
    _observers: ClassVar[List[Type["FieldsObserver"]]] = []

    @classmethod
    def register_observer(cls, observer: Type["FieldsObserver"]):
        cls._observers.append(observer)

    @classmethod
    def register_all(cls):
        for observer in cls._observers:
            observer.connect()


register_observer = FieldsObserverRegistry.register_observer


class FieldsObserver(BaseModel, Generic[InstanceType]):
    _observed_model: ClassVar[Type[InstanceType]] = PrivateAttr()
    observed_fields: ClassVar[List[str]] = Field(default_factory=list)

    @staticmethod
    def get_fields(
        observerd_fields: List[str],
        condition: Callable[[str], bool] = lambda field: True,
    ) -> List[str]:
        return [field_name for field_name in observerd_fields if condition(field_name)]

    @staticmethod
    def get_changed_fields(
        old_instance: InstanceType,
        new_instance: InstanceType,
        observed_fields: List[str],
    ) -> List[str]:
        return [
            field_name
            for field_name in observed_fields
            if getattr(old_instance, field_name) != getattr(new_instance, field_name)
        ]

    @classmethod
    def get_m2m_fields(cls):
        condition = (  # noqa
            lambda field_name: (field := cls._observed_model._meta.get_field(field_name)).is_relation
            and field.many_to_many
        )
        return cls.get_fields(cls.get_observed_fields(), condition)

    @classmethod
    def get_non_many_relation_fields(cls):
        condition = (  # noqa
            lambda field_name: not (field := cls._observed_model._meta.get_field(field_name)).is_relation
            or field.many_to_one
        )

        return cls.get_fields(cls.get_observed_fields(), condition)

    @classmethod
    def get_observed_fields(cls) -> List[str]:
        return cls.get_observed_fields()

    @classmethod
    def fields_changed(cls, *args, sender, old_instance, new_instance, changed_fields, **kwargs):
        pass

    @classmethod
    def connect_many_to_many_observer(cls, field_name):
        assert (field := cls._observed_model._meta.get_field(field_name)).is_relation and field.many_to_many

        through = field.remote_field.through

        def m2m_observer(instance, action: M2mChangedActions, **kwargs):
            if action not in ["post_add", "post_remove", "post_clear"]:
                return

            cls.fields_changed(
                sender=cls._observed_model,
                instance=instance,
                changed_fields=[field_name],
            )

        return m2m_changed.connect(m2m_observer, sender=through)

    @classmethod
    def connect_non_many_observer(cls, field_names):
        def pre_save_observer(sender, instance, **kwargs):
            old_instance = cls._observed_model.objects.filter(pk=instance.pk).first()
            new_instance = instance
            changed_fields = ["*"]

            if old_instance and not (changed_fields := cls.get_changed_fields(old_instance, new_instance, field_names)):
                return

            context = getattr(instance, FLEX_OBSERVER_CONTEXT_NAME, {})
            context["changed_fields"] = changed_fields
            setattr(instance, FLEX_OBSERVER_CONTEXT_NAME, context)

        def post_save_observer(sender, instance, **kwargs):
            if changed_fields := getattr(instance, FLEX_OBSERVER_CONTEXT_NAME, {}).get("changed_fields"):
                cls.fields_changed(
                    sender=sender,
                    instance=instance,
                    changed_fields=changed_fields,
                )

        def post_delete_observer(sender, instance, **kwargs):
            cls.fields_changed(
                sender=sender,
                instance=instance,
                changed_fields=["*"],
            )

        pre_save.connect(pre_save_observer, sender=cls._observed_model)
        post_save.connect(post_save_observer, sender=cls._observed_model)
        post_delete.connect(post_delete_observer, sender=cls._observed_model)

    @classmethod
    def connect(cls):
        for field_name in cls.get_m2m_fields():
            cls.connect_many_to_many_observer(field_name)

        cls.connect_non_many_observer(cls.get_non_many_relation_fields())
