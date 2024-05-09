from functools import lru_cache

import graphene
from graphene_django.converter import convert_choice_field_to_enum

import django.apps
from django.db.models.constants import LOOKUP_SEP

from .errors import EXCEPTION_ERROR_MAP, EXCEPTION_ERROR_TEXT_MAP, Error, Errors
from .models import FileModel


def get_all_subclasses(klass):
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
    return LOOKUP_SEP.join([field.field.name for field in fields])


def fix_array_choice_type(field):
    return graphene.List(convert_choice_field_to_enum(field.base_field))


def fix_array_choice_type_fields(*fields):
    return {field.name: fix_array_choice_type(field) for field in fields}


def get_file_models():
    return (model for model in django.apps.apps.get_models() if issubclass(model, FileModel))


def get_file_model(slug: str):
    return next((model for model in get_file_models() if model.SLUG == slug), None)
