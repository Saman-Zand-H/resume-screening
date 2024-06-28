from functools import wraps
from operator import call
from typing import Any, Callable, Dict

import graphene
from common.exceptions import GraphQLErrorBadRequest
from graphene.types.resolver import get_default_resolver
from graphene.types.utils import yank_fields_from_attrs
from graphene_django_cud.mutations import DjangoPatchMutation
from rules.rulesets import test_rule

from django.template.loader import render_to_string

from .accesses import AccessType
from .constants import VERIFICATION_EMAIL_FROM, VERIFICATION_PHONE_FROM
from .tasks import send_email_async
from .utils import IDLikeObject


class AccessRequiredMixin:
    @classmethod
    def has_access(cls, access_slug: str, **kwargs):
        if not test_rule(access_slug, **kwargs):
            cls.access_denied()

    @classmethod
    def get_rule_object(cls, info, *args, **kwargs) -> Dict[str, Any]:
        return {}

    @classmethod
    def access_denied(cls, access_slug: str):
        raise PermissionError("You don't have permission to perform this action.")

    @classmethod
    def get_user(cls, info, *args, **kwargs):
        if not getattr(info, "context", False):
            return

        return info.context.user


class MutationAccessRequiredMixin(AccessRequiredMixin):
    access: AccessType = None

    @classmethod
    def mutate(cls, root, info, *args, **kwargs):
        has_access_kwargs = cls.get_rule_object() or {}
        if user := cls.get_user(info, *args, **kwargs):
            has_access_kwargs["user"] = user

        access_denied_value, denied_has_value = cls.has_access(cls.access.slug, **has_access_kwargs)
        if denied_has_value:
            return access_denied_value

        return super().mutate(root, info, *args, **kwargs)


class ObjectTypeAccessRequiredMixin(AccessRequiredMixin):
    field_access_slugs: Dict[str, AccessType] = {}

    @classmethod
    def resolver_wrapper(cls, field_name: str) -> Callable:
        def wrapper(resolver: Callable) -> Callable:
            @wraps(resolver)
            def inner_wrapper(root, info, *args, **kwargs):
                has_access_kwargs = cls.get_rule_object(root, info, *args, **kwargs)
                if user := cls.get_user(info, *args, **kwargs):
                    has_access_kwargs["user"] = user

                cls.has_access(cls.field_access_slugs.get(field_name), **has_access_kwargs)

                return resolver(root, info, *args, **kwargs)

            return inner_wrapper

        return wrapper

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        attr_fields = yank_fields_from_attrs(cls.__dict__, _as=graphene.Field)
        registered_field_resolvers = set()

        for field_name, graphene_field in attr_fields.items():
            if getattr(graphene_field, "resolver", False):
                wrapper = cls.resolver_wrapper(field_name)
                setattr(cls, f"resolve_{field_name}", wrapper(graphene_field.resolver))
                registered_field_resolvers.add(field_name)
                continue

            if resolver := getattr(cls, f"resolve_{field_name}", False):
                wrapper = cls.resolver_wrapper(field_name)
                setattr(cls, f"resolve_{field_name}", wrapper(resolver))
                registered_field_resolvers.add(field_name)

        if len(cls.field_access_slugs) != len(registered_field_resolvers):
            kwargs.update(default_resolver=wrapper(kwargs.get("default_resolver", get_default_resolver())))

        super().__init_subclass_with_meta__(*args, **kwargs)


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
