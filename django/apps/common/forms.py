from datetime import datetime
from typing import Literal, Optional, Union, get_args, get_origin

from pydantic import BaseModel, HttpUrl

from django import forms


class WebhookForm(forms.Form):
    model = BaseModel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_fields_from_model(self.model)

    def add_field(self, field_name, field_type):
        field = self.create_form_field(field_type)
        if field:
            self.fields[field_name] = field

    def add_fields_from_model(self, model: BaseModel):
        for field_name, field_type in model.__annotations__.items():
            field = self.create_form_field(field_type)
            if field:
                self.fields[field_name] = field

    def create_form_field(self, field_type):
        is_optional = get_origin(field_type) is Optional or get_origin(field_type) is Union
        if is_optional:
            field_type = get_args(field_type)[0]

        if field_type in {str, int, float, bool, datetime, HttpUrl}:
            field_class = {
                str: forms.CharField,
                int: forms.IntegerField,
                float: forms.FloatField,
                bool: forms.BooleanField,
                datetime: forms.DateTimeField,
                HttpUrl: forms.URLField,
            }[field_type]
            return field_class(required=not is_optional)

        if get_origin(field_type) is Literal:
            choices = [(choice, choice) for choice in get_args(field_type)]
            return forms.ChoiceField(choices=choices, required=not is_optional)

        return forms.JSONField(required=not is_optional)
