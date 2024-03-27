from common.exceptions import GraphQLErrorBadRequest
from graphene_django_cud.mutations import DjangoPatchMutation

from .models import (
    DocumentAbstract,
)
from .utils import IDLikeObject


class DocumentCUDMixin:
    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        kwargs.update(
            {
                "login_required": True,
            }
        )
        return super().__init_subclass_with_meta__(*args, **kwargs)

    @classmethod
    def full_clean(cls, obj):
        obj.full_clean()


class DocumentCUDFieldMixin:
    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        kwargs.update(
            {
                "fields": (
                    *kwargs.get("fields", ()),
                    DocumentAbstract.allow_self_verification.field.name,
                ),
            }
        )
        return super().__init_subclass_with_meta__(*args, **kwargs)


class DocumentCheckPermissionsMixin(DocumentCUDMixin):
    @classmethod
    def check_permissions(cls, *args):
        info, obj = args[1], args[-1]
        if obj.user != info.context.user:
            raise PermissionError("Not permitted to modify this record.")

        if obj.status != DocumentAbstract.Status.DRAFTED:
            raise GraphQLErrorBadRequest("Only drafted documents can be modified.")

        return super().check_permissions(*args)


class DocumentUpdateMutationMixin(DocumentCheckPermissionsMixin, DocumentCUDMixin):
    @classmethod
    def update_obj(cls, *args, **kwargs):
        obj = super().update_obj(*args, **kwargs)
        cls.full_clean(obj)
        return obj


class FilterQuerySetByUserMixin:
    @classmethod
    def get_queryset(cls, queryset, info):
        user = info.context.user
        if not user:
            return queryset.none()
        return super().get_queryset(queryset, info).filter(user=user)


class UpdateStatusMixin(DjangoPatchMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        model = kwargs.get("model")
        kwargs.update(
            {
                "login_required": True,
                "type_name": f"Patch{model.__name__}StatusInput",
                "fields": (model.status.field.name,),
            }
        )
        return super().__init_subclass_with_meta__(*args, **kwargs)


class CRUDWithoutIDMutationMixin:
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        super().__init_subclass_with_meta__(*args, **kwargs)
        del cls._meta.arguments["id"]

    @classmethod
    def get_object_id(cls, info: IDLikeObject):
        raise NotImplementedError

    @classmethod
    def resolve_id(cls, info: IDLikeObject):
        if isinstance(info, IDLikeObject):
            info._id = cls.get_object_id(info.context)
            return info._id
        return info

    @classmethod
    def mutate(cls, *args, **kwargs):
        info = args[1]
        return super().mutate(*args, **kwargs, id=IDLikeObject(info))
