from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment
import google.auth

from django.conf import settings


def create_recaptcha_assessment(token: str, recaptcha_action: str) -> Assessment:
    _, project_id = google.auth.default()

    try:
        recaptcha_key = settings.RECAPTCHA_KEY
    except AttributeError:
        return

    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()

    event = recaptchaenterprise_v1.Event()
    event.site_key = recaptcha_key
    event.token = token

    assessment = recaptchaenterprise_v1.Assessment()
    assessment.event = event

    project_name = f"projects/{project_id}"

    request = recaptchaenterprise_v1.CreateAssessmentRequest()
    request.assessment = assessment
    request.parent = project_name

    try:
        response = client.create_assessment(request)
    except google.api_core.exceptions.InvalidArgument:
        return

    if not response.token_properties.valid:
        return

    if response.token_properties.action != recaptcha_action:
        return
    return response
