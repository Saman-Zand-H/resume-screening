from django import forms
from django.contrib.auth import get_user_model

from .models import Campaign


class CampaignNotifyConfirmForm(forms.Form):
    pass


class CampaignNotifyUserForm(forms.Form):
    users = forms.ModelMultipleChoiceField(queryset=get_user_model().objects.none())

    def __init__(self, *args, **kwargs):
        campaign: Campaign | None = kwargs.pop("campaign", None)
        super().__init__(*args, **kwargs)

        if campaign:
            self.fields["users"].queryset = campaign.saved_filter.get_queryset()
