from common.forms import WebhookForm

from .client.types import GetScoresResponse, GetStatusResponse


class ScoreWebhookForm(WebhookForm):
    model = GetScoresResponse


class StatusWebhookForm(WebhookForm):
    model = GetStatusResponse
