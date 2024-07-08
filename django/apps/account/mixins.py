from operator import call
from typing import Any, Dict, List

from common.exceptions import GraphQLErrorBadRequest
from graphene_django_cud.mutations import DjangoPatchMutation
from rules.rulesets import test_rule

from django.template.loader import render_to_string

from .accesses import AccessType
from .constants import VERIFICATION_EMAIL_FROM, VERIFICATION_PHONE_FROM
from .tasks import send_email_async
from .utils import IDLikeObject


class AccessRequiredMixin:
    @classmethod
    def has_item_access(cls, access_slug, info, **kwargs):
        from .models import User

        has_access_kwargs = cls.get_has_access_kwargs(access_slug, info, **kwargs)
        user: User = has_access_kwargs.get("user")
        if not user:
            return

        return user.has_access(access_slug) and test_rule(access_slug, has_access_kwargs)

    @classmethod
    def has_access(cls, accesses: List[AccessType], info, **kwargs):
        if not any(cls.has_item_access(access.slug, info, **kwargs) for access in accesses):
            cls.access_denied(accesses)

    @classmethod
    def get_rule_object(cls, info=None, *args, **kwargs) -> Dict[str, Any]:
        return {}

    @classmethod
    def access_denied(cls, access_slug: str):
        raise PermissionError("You don't have permission to perform this action.")

    @classmethod
    def get_has_access_kwargs(cls, access_slug: str, info, **kwargs):
        return {"instance": cls.get_rule_object(info), "user": cls.get_user(info), "access_slug": access_slug, **kwargs}

    @classmethod
    def get_user(cls, info, *args, **kwargs):
        if not getattr(info, "context", False):
            return

        return info.context.user


class MutationAccessRequiredMixin(AccessRequiredMixin):
    accesses: List[AccessType] = []

    @classmethod
    def mutate(cls, root, info, *args, **kwargs):
        cls.has_access(cls.accesses, info)

        return super().mutate(root, info, *args, **kwargs)


class EmailVerificationMixin:
    _verification_email_field_name: str = "email"
    _verification_template_name: str = ""
    _verification_subject: str = ""
    _verification_email_from: str = VERIFICATION_EMAIL_FROM

    def get_verification_context_data(self, **kwargs):
        return kwargs | {
            "cpj_email": self.get_verification_email_from(),
            "cpj_phone": VERIFICATION_PHONE_FROM,
        }

    def get_verification_email(self) -> str:
        if not (email := getattr(self, self._verification_email_field_name, None)):
            raise ValueError("Email field not found.")

        return email

    def get_verification_template_name(self):
        return self._verification_template_name

    def get_verification_subject(self):
        return self._verification_subject

    def get_verification_email_from(self):
        return self._verification_email_from

    def get_verification_content(self):
        return render_to_string(self.get_verification_template_name(), self.get_verification_context_data())

    def get_file_model_ids(self):
        return []

    def send_verification(self, *, is_async=True):
        email = self.get_verification_email()
        from_email = self.get_verification_email_from()
        subject = self.get_verification_subject()
        content = self.get_verification_content()

        call(
            getattr(send_email_async, is_async and "delay" or "__call__", "__call__"),
            recipient_list=[email],
            subject=subject,
            content=content,
            from_email=from_email,
            file_model_ids=self.get_file_model_ids(),
        )


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
        from .models import DocumentAbstract

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
        from .models import DocumentAbstract

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
    def get_object_id(cls, context: IDLikeObject):
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
        return super().mutate(*args, **kwargs, id=IDLikeObject({"info": info, "input": kwargs.get("input")}))
