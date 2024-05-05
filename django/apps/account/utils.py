import json
from typing import Any, Dict, List, Optional

from ai.google import GoogleServices
from ai.openai import OpenAIService
from common.models import Job, Skill
from config.settings.constants import Environment

from django.conf import settings
from django.db import transaction

from .constants import OpenAiAssistants, VectorStores


def get_additional_input_string(additional_input: Dict[str, Any]):
    return f"\n{"-"*20}\n".join(f"{k}: {v}" for k, v in additional_input.items())


def extract_job_additional_input(user):
    profile = user.profile
    return {
        "skills": ", ".join(user.skills.values_list("title", flat=True)),
        "languages": ", ".join(filter(bool, [profile.native_language, *profile.fluent_languages])),
        "certifications": ", ".join(user.certificateandlicenses.values_list("title", flat=True)),
        "educations": ", ".join(education.title for education in user.educations.all()),
        "work_experiences": ", ".join(experience.job.title for experience in user.workexperiences.all()),
    }


def extract_skills_additional_input(user):
    profile = user.profile
    return {
        "languages": ", ".join(filter(bool, [profile.native_language, *profile.fluent_languages])),
        "certifications": ", ".join(user.certificateandlicenses.values_list("title", flat=True)),
        "educations": ", ".join(education.title for education in user.educations.all()),
        "work_experiences": ", ".join(experience.job.title for experience in user.workexperiences.all()),
    }


def extract_resume_text(file: bytes) -> Optional[str]:
    ocr = GoogleServices.file_to_text(file)
    if ocr:
        return ocr.text
    return None


def extract_available_jobs(resume_text: str, user) -> Optional[List[Job]]:
    if not resume_text:
        return None
    service = OpenAIService(OpenAiAssistants.JOB)
    service.assistant_vector_store_update_cache(VectorStores.JOB)
    message_text = f"{resume_text}\n\n{get_additional_input_string(extract_job_additional_input(user))}"
    message = service.send_text_to_assistant(message_text)
    if message:
        try:
            return Job.objects.filter(pk__in=[j["pk"] for j in service.message_to_json(message)])
        except ValueError:
            return None
    return None


def extract_or_create_skills(skills: List[str], user) -> Optional[List[Skill]]:
    if not skills:
        return None

    service = OpenAIService(OpenAiAssistants.SKILL)
    service.assistant_vector_store_update_cache(VectorStores.SKILL)
    message_text = f'{{ "skills": [{", ".join(skills)}], "additional_input": {json.dumps(extract_skills_additional_input(user))} }}'
    message = service.send_text_to_assistant(message_text)

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


def is_env(env: Environment):
    return settings.ENVIRONMENT_NAME.value == env.value


class IDLikeObject:
    _id = None
    context = None

    def __init__(self, context):
        self.context = context

    def __repr__(self):
        return repr(self._id)
