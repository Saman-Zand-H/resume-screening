from typing import List, Optional

from ai.google import GoogleServices
from ai.openai import OpenAIService
from common.models import Job, Skill

from django.db import transaction

from .constants import OpenAiAssistants, VectorStores


def extract_resume_text(file: bytes) -> Optional[str]:
    ocr = GoogleServices.file_to_text(file)
    if ocr:
        return ocr.text
    return None


def extract_available_jobs(resume_text: str) -> Optional[List[Job]]:
    if not resume_text:
        return None
    service = OpenAIService(OpenAiAssistants.JOB)
    service.assistant_vector_store_update_cache(VectorStores.JOB)
    message = service.send_text_to_assistant(resume_text)
    if message:
        try:
            return Job.objects.filter(pk__in=[j["pk"] for j in service.message_to_json(message)])
        except ValueError:
            return None
    return None


def extract_or_create_skills(skills: List[str]) -> Optional[List[Skill]]:
    if not skills:
        return None

    service = OpenAIService(OpenAiAssistants.SKILL)
    service.assistant_vector_store_update_cache(VectorStores.SKILL)
    message = service.send_text_to_assistant(f"[{", ".join(skills)}]")

    if message:
        try:
            response = service.message_to_json(message)
            existing_skills, new_skills = response["similar_skills"], response["new_skills"]
            existing_skills = Skill.objects.filter(pk__in=[s["pk"] for s in existing_skills])
            with transaction.atomic():
                skills = Skill.objects.filter(
                    pk__in=[
                        s[0].pk
                        for s in [
                            Skill.objects.get_or_create(
                                title=s, defaults={Skill.insert_type.field.name: Skill.InsertType.AI}
                            )
                            for s in new_skills
                        ]
                    ]
                )
                existing_skills = (existing_skills | skills).system().distinct()
                new_skills = skills.ai()
                return existing_skills, new_skills
        except ValueError:
            return None
