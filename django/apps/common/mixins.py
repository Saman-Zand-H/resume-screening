from datetime import date, datetime

import graphene
import graphene_django
from config.settings.constants import Environment
from config.utils import is_env, is_recaptcha_token_valid
from graphene_django_cud.mutations.core import DjangoCudBaseOptions
from graphene_django_cud.util import to_snake_case

from common.utils import fix_array_choice_type, fix_array_choice_type_fields
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db.models.fields.related import RelatedField
from django.utils.translation import gettext_lazy as _

from .models import FileModel
from .utils import get_file_models


class HasDurationMixin:
    start_date_field: str = "start"
    end_date_field: str = "end"
    output_format: str = "%b %Y"

    def get_start_date(self) -> datetime | date:
        return getattr(self, self.start_date_field, None)

    def get_end_date(self) -> datetime | date:
        return getattr(self, self.end_date_field, None)

    def get_output_format(self) -> str:
        return self.output_format

    @property
    def duration(self):
        start_date = self.get_start_date()
        end_date = self.get_end_date()
        output_format = self.get_output_format()

        start_str = start_date.strftime(output_format) if start_date else ""
        end_str = end_date.strftime(output_format) if end_date else "Present"

        return f"{start_str} - {end_str}" if start_str and end_str else start_str or end_str

    duration.fget.verbose_name = _("Duration")


class ArrayChoiceTypeMixin:
    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        class_type = cls._meta.class_type
        model = kwargs.get("model")
        fields = kwargs.get("fields")

        if model:
            array_choice_fields = [
                field
                for field in model._meta.fields
                if field.name in fields and isinstance(field, ArrayField) and getattr(field.base_field, "choices")
            ]

            match class_type:
                case graphene_django.types.DjangoObjectType:
                    for field in array_choice_fields:
                        setattr(cls, field.name, fix_array_choice_type(field))
                case graphene.Mutation:
                    kwargs.update({"field_types": fix_array_choice_type_fields(*array_choice_fields)})
                    for field in array_choice_fields:
                        setattr(cls, f"handle_{field.name}", cls.handle_array_choice_field)

        return super().__init_subclass_with_meta__(*args, **kwargs)

    @classmethod
    def handle_array_choice_field(cls, value, *args, **kwargs):
        return [v.value for v in (value or [])]


class FilePermissionMixin:
    _file_fields: dict[str, FileModel] = {}

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        model = kwargs.get("model")
        fields = cls.get_fields(model)

        if model:
            file_models = set(get_file_models())
            cls._file_fields = {
                field.name: field.related_model
                for field in fields
                if isinstance(field, RelatedField)
                and any(issubclass(field.related_model, file_model) for file_model in file_models)
            }
        return super().__init_subclass_with_meta__(*args, **kwargs)

    @classmethod
    def get_fields(cls, model):
        return list(model._meta.fields)

    @classmethod
    def validate(cls, root, info, input, *args, **kwargs):
        cls._validate_file_permissions(info, input)
        if cls.is_django_cud_mutation():
            super().validate(root, info, input, *args, **kwargs)

    @classmethod
    def _validate_file_permissions(cls, info, input):
        for field, value in input.items():
            if field not in cls._file_fields:
                continue
            field_model = cls._file_fields.get(field)
            if not field_model:
                continue

            file_obj: FileModel = field_model.objects.filter(**{FileModel._meta.pk.attname: value}).first()
            if not file_obj:
                continue

            cls._check_file_permissions(file_obj, field, info)

    @classmethod
    def _check_file_permissions(cls, file_obj, field, info):
        if not file_obj.check_auth(info.context):
            raise PermissionError("You don't have permission to access this file.")

    @classmethod
    def mutate(cls, root, info, **kwargs):
        if not cls.is_django_cud_mutation():
            cls.validate(root, info, **kwargs)

        return super().mutate(root, info, **kwargs)

    @classmethod
    def is_django_cud_mutation(cls):
        return isinstance(cls._meta, DjangoCudBaseOptions)


class DocumentFilePermissionMixin(FilePermissionMixin):
    @classmethod
    def get_fields(cls, model):
        fields = super().get_fields(model)
        if hasattr(model, "get_method_models"):
            fields.extend([field for m in model.get_method_models() for field in m._meta.fields])
        return fields

    @classmethod
    def _validate_file_permissions(cls, info, input):
        if not hasattr(input, "items"):
            return

        for field, value in input.items():
            if hasattr(value, "__dict__"):
                cls._validate_file_permissions(info, value)
                continue
            if field not in cls._file_fields:
                continue
            field_model = cls._file_fields.get(field)
            if not field_model:
                continue

            file_obj: FileModel = field_model.objects.filter(**{FileModel._meta.pk.attname: value}).first()
            if not file_obj:
                continue

            cls._check_file_permissions(file_obj, field, info)


class CUDOutputTypeMixin:
    output_type = None

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        assert cls.output_type, "output_type must be set."
        model = kwargs.get("model")
        base_field = graphene.List if any("Batch" in m.__name__ for m in cls.mro()) else graphene.Field
        output_field_name = to_snake_case(model.__name__) + ("s" if base_field is graphene.List else "")

        setattr(cls, output_field_name, base_field(cls.output_type))
        return super().__init_subclass_with_meta__(*args, output=cls, return_field_name=output_field_name, **kwargs)


class UserContextMixin:
    user_context_key: str

    @classmethod
    def get_user_context(cls, request):
        return getattr(request, cls.user_context_key, request.user)

    @classmethod
    def set_user_context(cls, request, user):
        setattr(request, cls.user_context_key, user)
        return request


class MutateDecoratorMixin:
    """Mixin to integrate decorators into class-based mutations."""

    _decorator = None

    @property
    def decorator(self):
        return self._decorator

    @decorator.setter
    def decorator(self, value):
        self._decorator = value

    @classmethod
    def mutate(cls, *args, **kwargs):
        return cls.decorator(super().mutate)(*args, **kwargs)


class ReCaptchaMixin:
    recaptcha_field = "g_recaptcha_token"

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        super().__init_subclass_with_meta__(*args, **kwargs)
        cls._meta.arguments.update({cls.recaptcha_field: graphene.String(required=True)})

    @classmethod
    def mutate(cls, *args, **kwargs):
        g_recaptcha_token = kwargs.pop(cls.recaptcha_field, None)
        cls._validate_recaptcha(g_recaptcha_token)
        return super().mutate(*args, **kwargs)

    @classmethod
    def _validate_recaptcha(cls, g_recaptcha_token):
        if is_env(Environment.LOCAL):
            return
        if not is_recaptcha_token_valid(g_recaptcha_token):
            raise ValidationError({cls.recaptcha_field: _("Invalid reCAPTCHA token.")})
