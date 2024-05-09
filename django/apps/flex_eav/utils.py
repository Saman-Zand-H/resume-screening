from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.utils.translation import gettext_lazy as _


def validate_field_exists(model_class: Model, field_name: str):
    try:
        model_class._meta.get_field(field_name)
    except FieldDoesNotExist:
        raise ValueError(_("Field does not exist on model"))
