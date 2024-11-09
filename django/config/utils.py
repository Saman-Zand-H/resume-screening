from operator import attrgetter

import google.auth
from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment

from django.conf import settings

from .settings.constants import Environment, RecaptchaAction


def get_recaptcha_site_key() -> str:
    try:
        return settings.RECAPTCHA_SITE_KEY
    except AttributeError:
        return ""


def create_recaptcha_assessment(token: str, recaptcha_action: RecaptchaAction) -> Assessment:
    _, project_id = google.auth.default()

    recaptcha_site_key = get_recaptcha_site_key()
    if not recaptcha_site_key:
        return

    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()

    event = recaptchaenterprise_v1.Event()
    event.site_key = recaptcha_site_key
    event.token = token

    assessment = recaptchaenterprise_v1.Assessment()
    assessment.event = event

    request = recaptchaenterprise_v1.CreateAssessmentRequest()
    request.assessment = assessment
    request.parent = f"projects/{project_id}"

    try:
        response = client.create_assessment(request)
    except google.api_core.exceptions.InvalidArgument:
        return

    if not response.token_properties.valid:
        return

    if response.token_properties.action != recaptcha_action.value:
        return

    return response


def is_recaptcha_token_valid(token: str, recaptcha_action: RecaptchaAction) -> bool:
    assessment = create_recaptcha_assessment(token, recaptcha_action)
    return assessment and assessment.risk_analysis.score >= 0.7


def is_env(*envs: Environment) -> bool:
    return settings.ENVIRONMENT_NAME.value in map(attrgetter("value"), envs)
