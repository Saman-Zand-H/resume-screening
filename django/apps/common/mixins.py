from datetime import date, datetime

import graphene
import graphene_django
from common.utils import fix_array_choice_type, fix_array_choice_type_fields
from graphene_django_cud.mutations.core import DjangoCudBaseOptions

from django.contrib.postgres.fields import ArrayField
from django.db.models.fields.related import RelatedField
from django.forms import ValidationError
from django.utils.functional import cached_property

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

    @cached_property
    def duration(self):
        start_date = self.get_start_date()
        end_date = self.get_end_date()
        output_format = self.get_output_format()

        start_str = start_date.strftime(output_format) if start_date else ""
        end_str = end_date.strftime(output_format) if end_date else ""

        return f"{start_str} - {end_str}" if start_str and end_str else start_str or end_str


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
                if field.name in fields and isinstance(field, ArrayField) and hasattr(field.base_field, "choices")
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
        return [v.value for v in value]


class FilePermissionMixin:
    _file_fields: dict[str, FileModel] = {}

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        model = kwargs.get("model")
        fields = kwargs.get("fields")

        if model:
            file_models = set(get_file_models())
            cls._file_fields = {
                field.name: field.related_model
                for field in model._meta.fields
                if isinstance(field, RelatedField)
                and field.name in fields
                and any(issubclass(field.related_model, file_model) for file_model in file_models)
            }
        return super().__init_subclass_with_meta__(*args, **kwargs)

    @classmethod
    def validate(cls, root, info, input, *args, **kwargs):
        for field, value in input.items():
            if field not in cls._file_fields:
                continue
            field_model = cls._file_fields.get(field)
            if not field_model:
                continue

            file_obj: FileModel = field_model.objects.filter(pk=value).first()
            if not file_obj:
                continue

            cls._validate_file_permissions(file_obj, field, info)

        if cls.is_django_cud_mutation():
            super().validate(root, info, input, *args, **kwargs)

    @classmethod
    def _validate_file_permissions(cls, file_obj, field, info):
        if not file_obj.check_auth(info.context):
            raise PermissionError("You don't have permission to access this file.")

        if not file_obj.get_user_temporary_file(info.context.user) and not file_obj.is_used(info.context.user):
            raise ValidationError({field: "You can't use this file."})

    @classmethod
    def mutate(cls, root, info, **kwargs):
        if not cls.is_django_cud_mutation():
            cls.validate(root, info, **kwargs)

        return super().mutate(root, info, **kwargs)

    @classmethod
    def is_django_cud_mutation(cls):
        return isinstance(cls._meta, DjangoCudBaseOptions)