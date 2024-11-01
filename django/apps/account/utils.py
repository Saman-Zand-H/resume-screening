import contextlib
import json
from itertools import chain
from operator import attrgetter
from typing import Any, List, Literal, Optional

from ai.google import GoogleServices
from cities_light.models import City
from common.models import Job, LanguageProficiencyTest, Skill, University
from common.utils import fields_join, get_file_model_mimetype
from config.settings.constants import Assistants, Environment
from flex_blob.models import FileModel
from google.genai import types
from pydantic import ValidationError as PydanticValidationError

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.expressions import ArraySubquery
from django.db import transaction
from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import JSONObject

from .constants import FileSlugs, VectorStores
from .typing import (
    AnalysisResponse,
    ResumeJson,
)


def set_contacts_from_resume_json(user, resume_json: dict):
    from .models import Contact, Contactable, Profile

    contactable = Contactable.objects.filter(
        **{fields_join(Profile.contactable.field.related_query_name(), Profile.user): user}
    ).first()

    if not (contactable and (resume_json_model := ResumeJson.model_validate(resume_json)).contact_informations):
        return

    user_contact_types = Contact.objects.filter(**{fields_join(Contact.contactable): contactable}).values_list(
        fields_join(Contact.type), flat=True
    )
    contacts = [
        Contact(
            **{
                fields_join(Contact.contactable): contactable,
                fields_join(Contact.value): contact_information.value,
                fields_join(Contact.type): contact_information.type,
            }
        )
        for contact_information in resume_json_model.contact_informations
        if contact_information.type not in user_contact_types
    ]
    Contact.objects.bulk_create(contacts, ignore_conflicts=True)


def set_profile_from_resume_json(user, resume_json: dict):
    from .models import Profile

    changes = {}
    profile: Profile = user.profile
    if not (resume_json_model := ResumeJson.model_validate(resume_json)):
        return

    if resume_json_model.gender and not profile.gender:
        changes.update(**{fields_join(Profile.gender): resume_json_model.gender})

    if resume_json_model.birth_date and not profile.birth_date:
        changes.update(**{fields_join(Profile.birth_date): resume_json_model.birth_date})

    if not changes:
        return

    for key, value in changes.items():
        setattr(profile, key, value)

    profile.save(update_fields=changes.keys())


def analyze_document(
    file_model_id: int,
    verification_method_name: Literal[
        FileSlugs.EMPLOYER_LETTER,
        FileSlugs.PAYSTUBS,
        FileSlugs.EDUCATION_EVALUATION,
        FileSlugs.DEGREE,
        FileSlugs.LANGUAGE_CERTIFICATE,
        FileSlugs.CERTIFICATE,
    ],
) -> AnalysisResponse:
    if not (file_model := FileModel.objects.filter(pk=file_model_id).first()):
        return

    service = GoogleServices(Assistants.DOCUMENT_ANALYSIS)
    mime_type = get_file_model_mimetype(file_model)
    with file_model.file.open("rb") as file:
        content = file.file.read()

    results = service.generate_text_content(
        [
            types.Part.from_bytes(data=content, mime_type=mime_type),
            types.Part.from_text(text=json.dumps({"verification_method_name": verification_method_name})),
        ]
    )

    if results:
        with contextlib.suppress(PydanticValidationError):
            return AnalysisResponse.model_validate(service.message_to_json(results))

        return AnalysisResponse(is_valid=False)


def extract_resume_json(file_model_id: int):
    if not (file_model := FileModel.objects.filter(pk=file_model_id).first()):
        return

    service = GoogleServices(Assistants.RESUME_JSON)
    mime_type = get_file_model_mimetype(file_model)
    with file_model.file.open("rb") as file:
        content = file.file.read()

    results = service.generate_text_content(
        [
            types.Part.from_bytes(data=content, mime_type=mime_type),
            types.Part.from_text(text="extract resume JSON"),
        ]
    )

    if results:
        return service.message_to_json(results)


def get_user_additional_information(user_id: int, *, verified_work_experiences=True, verified_educations=True):
    from .models import (
        CertificateAndLicense,
        Education,
        LanguageCertificate,
        LanguageCertificateValue,
        LanguageProficiencySkill,
        Profile,
        User,
        WorkExperience,
    )

    user = User.objects.filter(pk=user_id).first()
    if not user:
        return {}

    profile: Profile = user.profile
    certifications = CertificateAndLicense.objects.filter(
        user=user,
        status__in=CertificateAndLicense.get_verified_statuses(),
    ).values(
        CertificateAndLicense.certificate_text.field.name,
        CertificateAndLicense.title.field.name,
        CertificateAndLicense.issued_at.field.name,
        CertificateAndLicense.certifier.field.name,
    )
    work_experiences = WorkExperience.objects.filter(
        user=user,
        status__in=WorkExperience.get_verified_statuses()
        if verified_work_experiences
        else map(attrgetter("value"), WorkExperience.Status),
    ).values(
        WorkExperience.job_title.field.name,
        WorkExperience.organization.field.name,
        WorkExperience.start.field.name,
        WorkExperience.end.field.name,
        fields_join(WorkExperience.city.field.name, City.display_name.field.name),
    )

    language_certificates_values = Subquery(
        LanguageCertificateValue.objects.filter(
            **{LanguageCertificateValue.language_certificate.field.name: OuterRef("pk")}
        ).values_list(
            JSONObject(
                **{
                    LanguageProficiencySkill.skill_name.field.name: F(
                        fields_join(LanguageCertificateValue.skill, LanguageProficiencySkill.skill_name)
                    ),
                    LanguageCertificateValue.value.field.name: F(LanguageCertificateValue.value.field.name),
                }
            ),
            flat=True,
        )
    )
    language_certificates = LanguageCertificate.objects.filter(
        user=user,
        status__in=LanguageCertificate.get_verified_statuses(),
    ).values(
        fields_join(LanguageCertificate.test, LanguageProficiencyTest.title),
        LanguageCertificate.language.field.name,
        LanguageCertificate.issued_at.field.name,
        scores=ArraySubquery(language_certificates_values),
    )

    educations = Education.objects.filter(
        user=user,
        status__in=Education.get_verified_statuses()
        if verified_educations
        else map(attrgetter("value"), Education.Status),
    ).values(
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
        "skills": profile.raw_skills,
    }

    if profile.city:
        additional_info["city"] = profile.city.display_name
        additional_info["country"] = profile.city.country.name

    if profile.gender:
        additional_info["gender"] = profile.get_gender_display()

    if profile.skills.exists():
        additional_info["skills"].extend(profile.skills.values_list("title", flat=True))

    return additional_info


def extract_available_jobs(resume_json: dict[str, Any], **additional_information) -> Optional[List[Job]]:
    if not resume_json:
        return None

    service = GoogleServices(Assistants.JOB)
    message_dict = {
        "resume_data": resume_json,
        **additional_information,
    }
    message = service.generate_text_content(
        [
            types.Part.from_text(text=json.dumps(message_dict)),
            types.Part.from_text(text="\nTHE FOLLOWING IS THE DATA:\n"),
            types.Part.from_text(text=json.dumps(VectorStores.JOB.data_fn())),
        ]
    )
    if message:
        return Job.objects.filter(pk__in=[j["pk"] for j in service.message_to_json(message)])

    return Job.objects.none()


def extract_certificate_text_content(file_model_id: int):
    if not (file_model := FileModel.objects.filter(pk=file_model_id).first()):
        return ""

    service = GoogleServices(Assistants.OCR)
    mimetype = get_file_model_mimetype(file_model)
    with file_model.file.open("rb") as file:
        content = file.file.read()

    results = service.generate_text_content(
        [
            types.Part.from_bytes(data=content, mime_type=mimetype),
            types.Part.from_text(text="extract text content"),
        ]
    )

    return results and service.message_to_json(results) or ""


def set_user_skills(user_id: int, raw_skills: List[str]) -> bool:
    user = get_user_model().objects.get(pk=user_id)
    resume_json = {} if not hasattr(user, "resume") else user.resume.resume_json
    profile = user.profile

    extracted_skills = extract_or_create_skills(
        raw_skills,
        resume_json,
        **get_user_additional_information(user_id),
    )

    profile.skills.clear() if not extracted_skills else profile.skills.set(chain.from_iterable(extracted_skills))
    return True


@transaction.atomic
def extract_or_create_skills(raw_skills: List[str], resume_json, **additional_information) -> Optional[List[Skill]]:
    if not (raw_skills or resume_json):
        return Skill.objects.none()

    service = GoogleServices(Assistants.SKILL)
    message_dict = {"raw_skills": raw_skills, "resume_data": resume_json, **additional_information}
    message = service.generate_text_content(
        [
            types.Part.from_text(text=json.dumps(message_dict)),
            types.Part.from_text(text="\nTHE FOLLOWING IS THE DATA:\n"),
            types.Part.from_text(text=json.dumps(VectorStores.SKILL.data_fn())),
        ]
    )

    if message:
        response = service.message_to_json(message)
        existing_skill_matches, new_skill_matches = response["matched_skills"], response["new_skills"]

        existing_skills = Skill.objects.filter(pk__in=[match.get("pk") for match in existing_skill_matches])
        created_skills = Skill.objects.filter(
            pk__in=[
                Skill.objects.get_or_create(
                    title=skill_name,
                    defaults={Skill.insert_type.field.name: Skill.InsertType.AI},
                )[0].pk
                for new_skill in new_skill_matches
                if (skill_name := new_skill.get("title"))
            ]
        )
        existing_skills = (existing_skills | created_skills).distinct()

        return existing_skills, created_skills.ai()

    return Skill.objects.none()


def is_env(*envs: Environment) -> bool:
    return settings.ENVIRONMENT_NAME.value in map(attrgetter("value"), envs)


class IDLikeObject:
    _id = None
    context = None

    def __init__(self, context):
        self.context = context

    def __repr__(self):
        return repr(self._id)
