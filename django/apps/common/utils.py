import contextlib
from functools import lru_cache, reduce
from typing import Dict, Set, List, Type

import graphene
from flex_blob.builders import BlobResponseBuilder
from graphene_django.converter import convert_choice_field_to_enum

import django.apps
from django.db.models import Model, OneToOneField
from django.db.models.constants import LOOKUP_SEP

from .constants import GRAPHQL_ERROR_FIELD_SEP
from .errors import EXCEPTION_ERROR_MAP, EXCEPTION_ERROR_TEXT_MAP, Error, Errors
from .models import FileModel


def merge_relations[T: Model](source: T, *target_objs: T, skipped_relations=[]):
    through_tables = [i.through for i in source._meta.related_objects if i.many_to_many]
    related_objects = [i for i in source._meta.related_objects if i.related_model not in through_tables]

    for relation in related_objects:
        for source_obj in target_objs:
            if relation.related_model in skipped_relations:
                continue

            if relation.one_to_many:
                with contextlib.suppress(AttributeError):
                    getattr(source, relation.get_accessor_name()).add(
                        *getattr(source_obj, relation.get_accessor_name()).all()
                    )

            elif relation.many_to_one or relation.one_to_one:
                setattr(source, relation.get_accessor_name(), getattr(source_obj, relation.get_accessor_name(), None))

            elif relation.many_to_many:
                getattr(source, relation.get_accessor_name()).add(
                    *getattr(source_obj, relation.get_accessor_name()).all()
                )

    return source


def seiralize_field_error(field_name: str, error_message: str) -> str:
    return "".join([field_name, GRAPHQL_ERROR_FIELD_SEP, error_message])


def field_serializer(field_name: str):
    def inner(error_message: str):
        return seiralize_field_error(field_name, error_message)

    return inner


def deserialize_field_error(field_error: str) -> Dict[str, str]:
    if not ((splitted_error := field_error.split(GRAPHQL_ERROR_FIELD_SEP)) and len(splitted_error) == 2):
        return field_error

    return dict(zip(["field", "error_message"], splitted_error))


def get_file_model_mimetype(file_model_instance: FileModel):
    blob_builder = BlobResponseBuilder.get_response_builder()
    return blob_builder.get_content_type(file_model_instance)


def nested_getattr(obj, attr, delimeter="."):
    return reduce(getattr, attr.split(delimeter), obj)


def get_all_subclasses[T](klass: T) -> Set[T]:
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses


@lru_cache(maxsize=None)
def map_exception_to_error(exception_class: type, exception_text: str = None) -> Error:
    if (exception_text) in EXCEPTION_ERROR_TEXT_MAP:
        return EXCEPTION_ERROR_TEXT_MAP[exception_text]
    else:
        if exception_class in tuple(EXCEPTION_ERROR_MAP):
            return EXCEPTION_ERROR_MAP[exception_class]
    return Errors.INTERNAL_SERVER_ERROR


def fields_join(*fields):
    return LOOKUP_SEP.join((hasattr(field, "field") and field.field.name) or field for field in fields)


def fix_array_choice_type(field):
    return graphene.List(convert_choice_field_to_enum(field.base_field))


def fix_array_choice_type_fields(*fields):
    return {field.name: fix_array_choice_type(field) for field in fields}


def get_file_models():
    return (model for model in django.apps.apps.get_models() if issubclass(model, FileModel))


def get_file_model(slug: str):
    return next((model for model in get_file_models() if model.SLUG == slug), None)


def get_verification_method_file_models(base_model: Type[Model]) -> List[Model]:
    return (
        field.related_model
        for model in base_model.get_method_models()
        for field in model._meta.fields
        if isinstance(field, OneToOneField) and issubclass(field.related_model, FileModel)
    )
