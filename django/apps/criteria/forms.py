from datetime import datetime
from typing import Literal, Optional, Union, get_args, get_origin

from django import forms
from pydantic import BaseModel, HttpUrl

from .client.types import CombinedScore, GetScoresResponse


class ScoreWebhookTestForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_fields_from_model(GetScoresResponse)

    def add_fields_from_model(self, model: BaseModel):
        for field_name, field_type in model.__annotations__.items():
            if field_name == "scores":
                self.add_fields_from_combined_score_model()
            else:
                field = self.create_form_field(field_type)
                if field:
                    self.fields[field_name] = field

    def add_fields_from_combined_score_model(self):
        for score_field, score_type in CombinedScore.__annotations__.items():
            field_key = f"scores_{score_field}"
            field = self.create_form_field(score_type)
            if field:
                self.fields[field_key] = field

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
