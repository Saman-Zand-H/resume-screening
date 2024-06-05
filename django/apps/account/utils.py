import json
from typing import Any, List, Optional

from ai.google import GoogleServices
from ai.openai import OpenAIService
from common.models import Job, Skill, University
from common.utils import fields_join
from config.settings.constants import Environment

from django.conf import settings
from django.db import transaction

from .constants import OpenAiAssistants, VectorStores
from .types.resume import ResumeSchema


def extract_resume_text(file: bytes) -> Optional[str]:
    ocr = GoogleServices.file_to_text(file)
    if ocr:
        return ocr.text
    return None


def extract_resume_json(text: str) -> Optional[ResumeSchema]:
    service = OpenAIService(OpenAiAssistants.RESUME)
    message = service.send_text_to_assistant(text)
    if message:
        json = service.message_to_json(message)
        return ResumeSchema.model_validate(json)


def get_user_additional_information(user_id: int):
    from .models import (
        CertificateAndLicense,
        Education,
        LanguageCertificate,
        User,
        WorkExperience,
    )

    user = User.objects.filter(pk=user_id).first()
    if not user:
        return {}

    profile = user.profile
    certifications = CertificateAndLicense.objects.filter(
        user=user,
        status__in=CertificateAndLicense.get_verified_statuses(),
    ).values(
        CertificateAndLicense.title.field.name,
        CertificateAndLicense.issued_at.field.name,
        CertificateAndLicense.certifier.field.name,
    )
    work_experiences = WorkExperience.objects.filter(
        user=user,
        status__in=WorkExperience.get_verified_statuses(),
    ).values(
        WorkExperience.job_title.field.name,
        WorkExperience.organization.field.name,
        WorkExperience.start.field.name,
        WorkExperience.end.field.name,
        WorkExperience.city.field.name,
    )
    language_certificates = [
        {"language": certificate.language, "scores": certificate.scores, "name": certificate.test.title}
        for certificate in LanguageCertificate.objects.filter(
            user=user,
            status__in=LanguageCertificate.get_verified_statuses(),
        ).all()
    ]
    educations = Education.objects.filter(user=user, status__in=Education.get_verified_statuses()).values(
        Education.degree.field.name,
        fields_join(Education.university, University.name),
        Education.city.field.name,
        Education.start.field.name,
        Education.end.field.name,
    )
    languages = list(filter(bool, [profile.native_language, *(profile.fluent_languages or [])]))
    additional_info = {
        "work_experiences": work_experiences,
        "educations": educations,
        "languages": languages,
        "certifications": certifications,
        "language_certificates": language_certificates,
    }

    if profile.city:
        additional_info["city"] = profile.city.display_name
        additional_info["country"] = profile.city.country.name

    if profile.gender:
        additional_info["gender"] = profile.get_gender_display()

    return additional_info


def extract_available_jobs(resume_json: dict[str, Any], **additional_information) -> Optional[List[Job]]:
    if not resume_json:
        return None

    service = OpenAIService(OpenAiAssistants.JOB)
    service.assistant_vector_store_update_cache(VectorStores.JOB)
    message_dict = {
        "resume_data": resume_json,
        **additional_information,
    }
    message = service.send_text_to_assistant(json.dumps(message_dict))
    if message:
        try:
            return Job.objects.filter(pk__in=[j["pk"] for j in service.message_to_json(message)])
        except ValueError:
            return None
    return None


def extract_or_create_skills(skills: List[str], resume_json, **additional_information) -> Optional[List[Skill]]:
    if not (skills or resume_json):
        return Skill.objects.none()

    service = OpenAIService(OpenAiAssistants.SKILL)
    service.assistant_vector_store_update_cache(VectorStores.SKILL)
    message_dict = {"raw_skills": skills, "resume_data": resume_json, **additional_information}
    message = service.send_text_to_assistant(json.dumps(message_dict))

    if message:
        try:
            response = service.message_to_json(message)
            existing_skills, new_skills = response["matched_skills"], response["new_skills"]
            existing_skills = Skill.objects.filter(pk__in=[s["pk"] for s in existing_skills])
            with transaction.atomic():
                skills = Skill.objects.filter(
                    pk__in=[
                        s[0].pk
                        for s in [
                            Skill.objects.get_or_create(
                                title__iexact=s.get("title"),
                                defaults={Skill.insert_type.field.name: Skill.InsertType.AI},
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

    return Skill.objects.none()


def is_env(env: Environment):
    return settings.ENVIRONMENT_NAME.value == env.value


class IDLikeObject:
    _id = None
    context = None

    def __init__(self, context):
        self.context = context

    def __repr__(self):
        return repr(self._id)
