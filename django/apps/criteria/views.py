import contextlib
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormView

from .forms import ScoreWebhookForm
from .webhooks import Events, WebhookHandler

logger = logging.getLogger(__name__)


class WebhookView(FormView):
    event = None
    form_class = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        with contextlib.suppress(json.JSONDecodeError):
            kwargs["data"] = json.loads(self.request.body.decode("utf-8"))
        return kwargs

    def get_error(self, message, status=400):
        return JsonResponse({"error": message}, status=status)

    def get_response(self, data, status=200):
        return JsonResponse(data, status=status)

    def post(self, request, *args, **kwargs):
        api_key = request.headers.get("x-criteria-api-key")
        if api_key is None or api_key != settings.CRITERIA_SETTINGS["WEBHOOK_SECRET"]:
            return self.get_error("Unauthorized", status=401)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        payload = form.cleaned_data
        try:
            payload_data = WebhookHandler.handle_event(self.event, payload)
            return self.get_response(payload_data)
        except ValueError as e:
            logger.error(f"Event handling error: {e}")
            return self.get_error(str(e))
        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            return self.get_error("Failed to process webhook", status=500)

    def form_invalid(self, form):
        return self.get_error("Invalid form data")


@method_decorator(csrf_exempt, name="dispatch")
class ScoresWebhookView(WebhookView):
    event = Events.SCORES_UPDATE
    form_class = ScoreWebhookForm
