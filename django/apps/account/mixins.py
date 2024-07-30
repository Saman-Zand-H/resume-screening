import warnings
from functools import wraps
from operator import call
from typing import Any, Callable

import graphene
from django.db import models
from common.exceptions import GraphQLErrorBadRequest
from graphene.types.resolver import get_default_resolver
from graphene.types.utils import yank_fields_from_attrs
from graphene_django_cud.mutations import DjangoPatchMutation
from graphql import GraphQLResolveInfo
from graphql_jwt.decorators import login_required
from rules.rulesets import test_rule

from django.template.loader import render_to_string

from .constants import VERIFICATION_EMAIL_FROM, VERIFICATION_PHONE_FROM
from .exceptions import AccessDenied
from .tasks import send_email_async
from .utils import IDLikeObject


class AccessRequiredMixin:
    @classmethod
    def has_access(cls, accesses, *args, **kwargs):
        if not any(cls.has_item_access(getattr(access, "slug", access), *args, **kwargs) for access in accesses):
            cls.access_denied(accesses)

    @classmethod
    def has_item_access(cls, access_slug, *args, **kwargs):
        from .models import User

        has_access_kwargs = cls.get_has_access_kwargs(access_slug, *args, **kwargs)
        user: User = has_access_kwargs.get("user")
        if not user:
            return

        return user.has_access(access_slug) and test_rule(access_slug, has_access_kwargs)

    @classmethod
    def get_access_object(cls, access_slug, *args, **kwargs) -> Any:
        return None

    @classmethod
    def access_denied(cls, access_slug: str):
        raise AccessDenied()

    @classmethod
    def get_has_access_kwargs(cls, access_slug, *args, **kwargs):
        return {
            "instance": cls.get_access_object(access_slug, *args, **kwargs),
            "user": cls.get_user(access_slug, *args, **kwargs),
        }

    @classmethod
    def get_info(cls, *args):
        return next((arg for arg in args if isinstance(arg, GraphQLResolveInfo)), None)

    @classmethod
    def get_obj_from_args(cls, args):
        return next((arg for arg in args if isinstance(arg, models.Model)), None)

    @classmethod
    def get_user(cls, *args, **kwargs):
        info = cls.get_info(*args)
        if not getattr(info, "context", False):
            return

        return info.context.user


class ObjectTypeAccessRequiredMixin(AccessRequiredMixin):
    fields_access = {}

    @classmethod
    def resolver_wrapper(cls, accesses) -> Callable:
        def wrapper(resolver: Callable):
            @wraps(resolver)
            @login_required
            def inner_wrapper(*args, **kwargs):
                try:
                    cls.has_access(
                        accesses,
                        *args,
                        **kwargs,
                    )
                    return resolver(*args, **kwargs)
                except AccessDenied as e:
                    if e.should_raise:
                        raise PermissionError(e.error_content)

                    return e.error_content

            return inner_wrapper

        return wrapper

    @classmethod
    def register_resolver(cls, field_name, accesses, graphene_field):
        resolver = getattr(
            cls,
            f"resolve_{field_name}",
            graphene_field.resolver if getattr(graphene_field, "resolver", False) else None,
        )
        if not resolver:
            return

        wrapper = cls.resolver_wrapper(accesses)
        setattr(cls, f"resolve_{field_name}", wrapper(resolver))

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        attr_fields = yank_fields_from_attrs(cls.__dict__, _as=graphene.Field)
        registered_field_resolvers = set()

        if "__all__" in cls.fields_access:
            accesses = cls.fields_access.get("__all__", [])
            for field_name, graphene_field in attr_fields.items():
                cls.register_resolver(field_name, accesses, graphene_field)
                registered_field_resolvers.add(field_name)

            kwargs.update(
                default_resolver=cls.resolver_wrapper(accesses)(
                    kwargs.get("default_resolver", get_default_resolver()),
                )
            )
            return super().__init_subclass_with_meta__(*args, **kwargs)

        for field_name, graphene_field in attr_fields.items():
            cls.register_resolver(field_name, cls.fields_access.get(field_name, []), graphene_field)
            registered_field_resolvers.add(field_name)

        if len(cls.fields_access) != len(registered_field_resolvers):
            differences = set(cls.fields_access.keys()) - registered_field_resolvers
            accesses = cls.fields_access.get(
                differences and differences[0] or cls.fields_access.get("__default__"),
                [],
            )
            kwargs.update(
                default_resolver=cls.resolver_wrapper(accesses)(kwargs.get("default_resolver", get_default_resolver()))
            )

        if abs(len(cls.fields_access) - len(registered_field_resolvers)) > 1:
            warnings.warn(
                "Some fields are not registered with access checks or "
                "multiple accesses are passed for default resolvers."
            )

        super().__init_subclass_with_meta__(*args, **kwargs)


class MutationAccessRequiredMixin(AccessRequiredMixin):
    accesses = []

    @classmethod
    def resolver_wrapper(cls, mutation: Callable):
        @wraps(mutation)
        @login_required
        def wrapper(root, info, *args, **kwargs):
            try:
                cls.has_access(cls.accesses, info, *args, **kwargs)
            except AccessDenied as e:
                if e.should_raise:
                    raise PermissionError(e.error_content)

                return e.error_content
            return mutation(root, info, *args, **kwargs)

        return wrapper

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        setattr(cls, "mutate", cls.resolver_wrapper(getattr(cls, "mutate", lambda *args, **kwargs: None)))

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
