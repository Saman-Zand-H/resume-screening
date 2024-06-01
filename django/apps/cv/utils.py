import json
import re

from account.constants import OpenAiAssistants
from account.utils import get_user_additional_information
from ai.openai import OpenAIService

from django.conf import settings


def extract_generated_resume_input(user):
    data = get_user_additional_information(user.id)

    if hasattr(user, "resume"):
        data["resume_data"] = user.resume.resume_json

    service = OpenAIService(OpenAiAssistants.GENERATE_RESUME)
    message = service.send_text_to_assistant(json.dumps(data))
    if message:
        print(message)
        try:
            return service.message_to_json(message)
        except ValueError:
            return None


def get_static_base_url():
    static_base_url = "http://localhost:8000"
    site_domain = settings.SITE_DOMAIN and re.sub(r"https?://", "", settings.SITE_DOMAIN)

    if site_domain and "localhost" not in site_domain:
        static_base_url = f"https://{settings.SITE_DOMAIN}"
    return static_base_url
