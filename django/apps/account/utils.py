from typing import List, Optional

from ai.google import GoogleServices
from ai.openai import OpenAIService
from common.models import Job

from .constants import OpenAiAssistants, VectorStores


def extract_resume_text(file: bytes) -> Optional[str]:
    ocr = GoogleServices.file_to_text(file)
    if ocr:
        return ocr.text
    return None


def extract_available_jobs(resume_text: str) -> Optional[List[Job]]:
    service = OpenAIService(OpenAiAssistants.JOB)
    service.assistant_vector_store_update_cache(VectorStores.JOB)
    message = service.send_text_to_assistant(resume_text)
    if message:
        try:
            return Job.objects.filter(pk__in=[j["pk"] for j in service.message_to_json(message)])
        except ValueError:
            return None
    return None
