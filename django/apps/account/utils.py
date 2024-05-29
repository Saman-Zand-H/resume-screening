import contextlib
import json
from typing import Any, List, Optional

from ai.google import GoogleServices
from ai.openai import OpenAIService
from common.models import Job, Skill
from config.settings.constants import Environment

from django.conf import settings

from .constants import OpenAiAssistants, VectorStores
from .types.resume import ResumeHeadlines, ResumeSchema


def extract_resume_headlines(resume_json: ResumeSchema) -> ResumeHeadlines:
    service = OpenAIService(OpenAiAssistants.HEADLINES)
    message = service.send_text_to_assistant(resume_json.model_dump_json())
    if message:
        with contextlib.suppress(ValueError):
            return ResumeHeadlines.model_validate(service.message_to_json(message))
    return None


def extract_job_additional_input(user):
    profile = user.get_profile()
    data = {
        "skills": ", ".join(profile.skills.values_list("title", flat=True)),
        "languages": ", ".join(filter(bool, [profile.native_language, *profile.fluent_languages])),
        "certifications": ", ".join(user.certificateandlicenses.values_list("title", flat=True)),
        "educations": ", ".join(education.title for education in user.educations.all()),
        "work_experiences": ", ".join(experience.job.title for experience in user.workexperiences.all()),
    }

    if hasattr(user, "resume"):
        data["resume_data"] = user.resume.resume_json

    return data


def extract_skills_additional_input(user):
    profile = user.get_profile()
    data = {
        "languages": ", ".join(filter(bool, [profile.native_language, *profile.fluent_languages])),
        "certifications": ", ".join(user.certificateandlicenses.values_list("title", flat=True)),
        "educations": ", ".join(education.title for education in user.educations.all()),
        "work_experiences": ", ".join(experience.job.title for experience in user.workexperiences.all()),
    }

    if hasattr(user, "resume"):
        data["resume_data"] = user.resume.resume_json

    return data


def extract_resume_text(file: bytes) -> Optional[str]:
    ocr = GoogleServices.file_to_text(file)
    if ocr:
        return ocr.text
    return None


def extract_resume_json(text: str) -> Optional[ResumeSchema]:
    service = OpenAIService(OpenAiAssistants.RESUME)
    message = service.send_text_to_assistant(text)
    if message:
        try:
            json = service.message_to_json(message)
            return ResumeSchema.model_validate(json)
        except ValueError:
            return None


def extract_available_jobs(resume_json: dict[str, Any]) -> Optional[List[Job]]:
    if not resume_json:
        return None

    service = OpenAIService(OpenAiAssistants.JOB)
    service.assistant_vector_store_update_cache(VectorStores.JOB)
    message = service.send_text_to_assistant(f'{{ "resume_data": {json.dumps(resume_json)} }}')
    if message:
        try:
            return Job.objects.filter(pk__in=[j["pk"] for j in service.message_to_json(message)])
        except ValueError:
            return None
    return None


def extract_or_create_skills(skills: List[str], resume_json) -> Optional[List[Skill]]:
    if not (skills or resume_json):
        return None

    service = OpenAIService(OpenAiAssistants.SKILL)
    service.assistant_vector_store_update_cache(VectorStores.SKILL)
    message_text = f'{{ "skills": [{", ".join(skills)}], "resume_data": {json.dumps(resume_json)} }}'
    message = service.send_text_to_assistant(message_text)

    if message:
        try:
            response = service.message_to_json(message)
            existing_skills = response["similar_skills"]
            return Skill.objects.filter(pk__in=[s["pk"] for s in existing_skills])
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
