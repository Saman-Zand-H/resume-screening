from common.utils import fix_array_choice_type_fields
from django.contrib.postgres.fields import ArrayField


class ArrayChoiceTypeMixin:
    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        model = kwargs.get("model")
        fields = kwargs.get("fields")

        if model:
            array_choice_fields = [
                field
                for field in model._meta.fields
                if field.name in fields and isinstance(field, ArrayField) and hasattr(field.base_field, "choices")
            ]
            kwargs.update({"field_types": fix_array_choice_type_fields(*array_choice_fields)})
            for field in array_choice_fields:
                setattr(cls, f"handle_{field.name}", cls.handle_array_choice_field)
        return super().__init_subclass_with_meta__(*args, **kwargs)

    @classmethod
    def handle_array_choice_field(cls, value, *args, **kwargs):
        return [v.value for v in value]


class FilePermissionMixin:
    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        from account.models import UserUploadedImageFile, UserUploadedDocumentFile

        model = kwargs.get("model")
        fields = kwargs.get("fields")

        
        file_fields = [
            field
            for field in model._meta.fields
            if (
                field.name in fields
                and hasattr(field, "related_model")
                and issubclass(field.related_model, (UserUploadedImageFile, UserUploadedDocumentFile))
            )
        ]

        for field in file_fields:
            if field.check_auth:
                raise PermissionError(f"Field {field.name} already has a check_auth method.")

        return super().__init_subclass_with_meta__(*args, **kwargs)
