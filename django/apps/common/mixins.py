import graphene
import graphene_django
from graphene_django_cud.mutations.core import DjangoCudBaseOptions

from common.utils import fix_array_choice_type, fix_array_choice_type_fields
from django.contrib.postgres.fields import ArrayField
from django.db.models.fields.related import RelatedField
from django.forms import ValidationError

from .models import FileModel
from .utils import get_file_models


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
        if file_obj.get_user_temprorary_file(info.context.user) or not file_obj.is_used(info.context.user):
            raise ValidationError({field: "You can't use this file."})

    @classmethod
    def mutate(cls, root, info, **kwargs):
        if not cls.is_django_cud_mutation():
            cls.validate(root, info, **kwargs)

        return super().mutate(root, info, **kwargs)

    @classmethod
    def is_django_cud_mutation(cls):
        return isinstance(cls._meta, DjangoCudBaseOptions)
