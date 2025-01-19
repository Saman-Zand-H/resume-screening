import contextlib
import json
from collections import defaultdict
from itertools import chain
from operator import attrgetter
from typing import List, Literal, Optional

import pydantic
from ai.assistants import AssistantPipeline
from ai.google import GoogleServices
from cities_light.models import City, Country
from common.models import LanguageProficiencyTest, Skill, University
from common.utils import fj
from config.settings.constants import Assistants
from google.genai import types

from django.contrib.auth import get_user_model
from django.contrib.postgres.expressions import ArraySubquery
from django.db import transaction
from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import JSONObject
from django.db.models.lookups import IContains, IExact, In

from .assistants import (
    DocumentDataAnalysisAssistant,
    DocumentOcrAssistant,
    DocumentValidationAssistant,
    LanguageCertificateAnalysisAssistant,
)
from .constants import FileSlugs, VectorStores
from .typing import (
    AnalysisResponse,
    ResumeJson,
)


def set_contacts_from_resume_json(user, resume_json: dict):
    from .models import Contact, Contactable, Profile

    contactable = Contactable.objects.filter(
        **{fj(Profile.contactable.field.related_query_name(), Profile.user): user}
    ).first()

    if not (contactable and (resume_json_model := ResumeJson.model_validate(resume_json)).contact_informations):
        return

    user_contact_types = Contact.objects.filter(**{fj(Contact.contactable): contactable}).values_list(
        fj(Contact.type), flat=True
    )
    contacts = [
        Contact(
            **{
                fj(Contact.contactable): contactable,
                fj(Contact.value): contact_information.value,
                fj(Contact.type): contact_information.type,
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
        changes.update(**{fj(Profile.gender): resume_json_model.gender})

    if resume_json_model.birth_date and not profile.birth_date:
        changes.update(**{fj(Profile.birth_date): resume_json_model.birth_date})

    if resume_json_model.city and not profile.city:
        search_results = City.objects.filter(
            **{
                fj(
                    City.name,
                    IContains.lookup_name,
                ): resume_json_model.city,
            }
        )
        if resume_json_model.country:
            search_results = search_results.filter(
                **{
                    fj(City.country, Country.name, IExact.lookup_name): resume_json_model.country,
                }
            )

        if search_results.exists():
            changes.update(**{fj(Profile.city): search_results.last()})

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
    assistants = [
        DocumentValidationAssistant().build(
            file_model_id=file_model_id,
            verification_method_name=verification_method_name,
        ),
        DocumentOcrAssistant().build(file_model_id=file_model_id, verification_method_name=verification_method_name),
    ]

    if verification_method_name == FileSlugs.LANGUAGE_CERTIFICATE.value:
        assistants.append(
            LanguageCertificateAnalysisAssistant().build(verification_method_name=verification_method_name)
        )
    else:
        assistants.append(DocumentDataAnalysisAssistant().build(verification_method_name=verification_method_name))

    results = AssistantPipeline(*assistants).run()

    with contextlib.suppress(pydantic.ValidationError):
        return AnalysisResponse.model_validate(defaultdict(list, results))

    return AnalysisResponse(is_valid=False)


def extract_resume_json(file_model_id: int):
    service = GoogleServices(Assistants.RESUME_JSON)

    if not (file_part := service.get_file_part(file_model_id)):
        return

    results = service.generate_text_content(
        [
            file_part,
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

    user = User.objects.filter(**{User._meta.pk.attname: user_id}).first()
    if not user:
        return {}

    profile: Profile = user.profile
    certifications = CertificateAndLicense.objects.filter(
        **{
            fj(CertificateAndLicense.user): user,
            fj(CertificateAndLicense.status, In.lookup_name): CertificateAndLicense.get_verified_statuses(),
        },
    ).values(
        CertificateAndLicense.certificate_text.field.name,
        CertificateAndLicense.title.field.name,
        CertificateAndLicense.issued_at.field.name,
        CertificateAndLicense.certifier.field.name,
    )
    work_experiences = WorkExperience.objects.filter(
        **{
            fj(WorkExperience.user): user,
            fj(WorkExperience.status, In.lookup_name): WorkExperience.get_verified_statuses()
            if verified_work_experiences
            else map(attrgetter("value"), WorkExperience.Status),
        },
    ).values(
        WorkExperience.job_title.field.name,
        WorkExperience.organization.field.name,
        WorkExperience.start.field.name,
        WorkExperience.end.field.name,
        fj(WorkExperience.city, City.display_name),
    )

    language_certificates_values = Subquery(
        LanguageCertificateValue.objects.filter(
            **{LanguageCertificateValue.language_certificate.field.name: OuterRef("pk")}
        ).values_list(
            JSONObject(
                **{
                    LanguageProficiencySkill.skill_name.field.name: F(
                        fj(LanguageCertificateValue.skill, LanguageProficiencySkill.skill_name)
                    ),
                    LanguageCertificateValue.value.field.name: F(LanguageCertificateValue.value.field.name),
                }
            ),
            flat=True,
        )
    )
    language_certificates = LanguageCertificate.objects.filter(
        **{
            fj(LanguageCertificate.user): user,
            fj(LanguageCertificate.status, In.lookup_name): LanguageCertificate.get_verified_statuses(),
        }
    ).values(
        fj(LanguageCertificate.test, LanguageProficiencyTest.title),
        LanguageCertificate.language.field.name,
        LanguageCertificate.issued_at.field.name,
        scores=ArraySubquery(language_certificates_values),
    )

    educations = Education.objects.filter(
        **{
            fj(Education.user): user,
            fj(Education.status, In.lookup_name): Education.get_verified_statuses()
            if verified_educations
            else map(attrgetter("value"), Education.Status),
        }
    ).values(
        Education.degree.field.name,
        fj(Education.university, University.name),
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
        "skills": list(profile.skills.values_list(fj(Skill.title), flat=True)),
    }

    if profile.city:
        additional_info["city"] = profile.city.display_name
        additional_info["country"] = profile.city.country.name

    if profile.gender:
        additional_info["gender"] = profile.get_gender_display()

    if profile.skills.exists():
        additional_info["skills"].extend(profile.skills.values_list("title", flat=True))

    return additional_info


def extract_certificate_text_content(file_model_id: int):
    service = GoogleServices(Assistants.OCR)

    if not (file_part := service.get_file_part(file_model_id)):
        return ""

    results = service.generate_text_content(
        [
            file_part,
            types.Part.from_text(text="extract text content"),
        ]
    )

    return results and service.message_to_json(results) or ""


def set_user_skills(user_id: int, raw_skills: List[str]) -> bool:
    from .models import Resume

    user = get_user_model().objects.get(pk=user_id)
    resume_json = {} if not hasattr(user, Resume.user.field.related_query_name()) else user.resume.resume_json
    profile = user.profile

    extracted_skills = extract_or_create_skills(
        raw_skills,
        resume_json,
        **get_user_additional_information(user_id),
    )

    profile.skills.clear() if not extracted_skills else profile.skills.set(chain(extracted_skills))
    return True


@transaction.atomic
def extract_or_create_skills(raw_skills: List[str], resume_json, **additional_information) -> Optional[List[Skill]]:
    if not (raw_skills or resume_json):
        return Skill.objects.none()

    related_skills_message = GoogleServices(Assistants.FIND_RELATIVE_SKILLS).generate_text_content(
        [
            types.Part.from_text(
                text=json.dumps({"raw_skills": raw_skills, "resume_data": resume_json, **additional_information})
            )
        ]
    )

    if related_skills_message and (related_skills := GoogleServices.message_to_json(related_skills_message)):
        get_or_create_skills_message = GoogleServices(Assistants.SKILL).generate_text_content(
            [
                types.Part.from_text(text=json.dumps(related_skills)),
                types.Part.from_text(text=json.dumps(VectorStores.SKILL.data_fn())),
            ]
        )

        if get_or_create_skills_message:
            get_or_create_skills = GoogleServices.message_to_json(get_or_create_skills_message)
            existing_skill_matches, new_skill_matches = (
                get_or_create_skills.get("matched_skills", []),
                get_or_create_skills.get("new_skills", []),
            )

            existing_skill_ids = [match.get("pk") for match in existing_skill_matches]
            new_skill_ids = [
                Skill.objects.get_or_create(
                    **{fj(Skill.title): skill_name},
                    defaults={fj(Skill.insert_type): Skill.InsertType.AI},
                )[0].pk
                for skill_name in new_skill_matches
            ]

            all_skill_ids = existing_skill_ids + new_skill_ids
            skills = Skill.objects.filter(**{fj(Skill._meta.pk.attname, In.lookup_name): all_skill_ids}).distinct()

            return skills

    return Skill.objects.none()


class IDLikeObject:
    _id = None
    context = None

    def __init__(self, context):
        self.context = context

    def __repr__(self):
        return repr(self._id)
