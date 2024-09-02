from functools import lru_cache, reduce
from typing import Dict, List, Set

import graphene
from flex_blob.builders import BlobResponseBuilder
from graphene_django.converter import convert_choice_field_to_enum

import django.apps
from django.db.models.constants import LOOKUP_SEP

from .constants import GRAPHQL_ERROR_FIELD_SEP
from .errors import EXCEPTION_ERROR_MAP, EXCEPTION_ERROR_TEXT_MAP, Error, Errors
from .models import FileModel


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


def fields_join(*fields, suffix_lookups: List[str] = []):
    return LOOKUP_SEP.join(
        [(hasattr(field, "field") and field.field.name) or field for field in fields] + suffix_lookups
    )


def fix_array_choice_type(field):
    return graphene.List(convert_choice_field_to_enum(field.base_field))


def fix_array_choice_type_fields(*fields):
    return {field.name: fix_array_choice_type(field) for field in fields}


def get_file_models():
    return (model for model in django.apps.apps.get_models() if issubclass(model, FileModel))


def get_file_model(slug: str):
    return next((model for model in get_file_models() if model.SLUG == slug), None)
