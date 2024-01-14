import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .client.webhooks import WebhookHandler
from .forms import ScoreWebhookTestForm

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ScoresUpdateWebhookView(View):
    def post(self, *args, **kwargs):
        form_data = ScoreWebhookTestForm(self.request.POST)
        if not form_data.is_valid():
            return JsonResponse({"error": "Invalid form data"}, status=400)

        payload = form_data.cleaned_data

        try:
            payload_data = WebhookHandler().handle_event("scores_update", payload)
            return JsonResponse(payload_data, status=200)
        except ValueError as e:
            logger.error(f"Event handling error: {e}")
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            return JsonResponse({"error": "Webhook processing failed"}, status=500)
