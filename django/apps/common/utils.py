from functools import lru_cache

from django.db.models.constants import LOOKUP_SEP

from .errors import EXCEPTION_ERROR_MAP, EXCEPTION_ERROR_TEXT_MAP, Error, Errors


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
