import json
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import NamedTuple

from ai.types import CachableVectorStore
from common.logging import get_logger
from common.models import Job, Skill
from disposable_email_domains import blocklist

from django.conf import settings

logger = get_logger()


class ProfileAnnotationNames(NamedTuple):
    IS_ORGANIZATION_MEMBER = "is_organization_member"
    HAS_PROFILE_INFORMATION = "has_profile_information"
    HAS_EDUCATION = "has_education"
    HAS_UNVERIFIED_EDUCATION = "has_unverified_education"
    HAS_WORK_EXPERIENCE = "has_work_experience"
    HAS_UNVERIFIED_WORK_EXPERIENCE = "has_unverified_work_experience"
    HAS_RESUME = "has_resume"
    HAS_CERTIFICATE = "has_certificate"
    HAS_LANGUAGE_CERTIFICATE = "has_language_certificate"
    HAS_SKILLS = "has_skills"
    HAS_CANADA_VISA = "has_canada_visa"
    HAS_INTERESTED_JOBS = "has_interested_jobs"
    LAST_LOGIN = "last_login_days"
    DATE_JOINED = "date_joined_days"
    STAGE_DATA = "stage_data"
    COMPLETED_STAGES = "completed_stages"
    INCOMPLETE_STAGES = "incomplete_stages"
    HAS_INCOMPLETE_STAGES = "has_incomplete_stages"


STAGE_ANNOTATIONS = [
    ProfileAnnotationNames.HAS_RESUME,
    ProfileAnnotationNames.HAS_PROFILE_INFORMATION,
    ProfileAnnotationNames.HAS_WORK_EXPERIENCE,
    ProfileAnnotationNames.HAS_UNVERIFIED_WORK_EXPERIENCE,
    ProfileAnnotationNames.HAS_EDUCATION,
    ProfileAnnotationNames.HAS_UNVERIFIED_WORK_EXPERIENCE,
    ProfileAnnotationNames.HAS_CERTIFICATE,
    ProfileAnnotationNames.HAS_LANGUAGE_CERTIFICATE,
    ProfileAnnotationNames.HAS_SKILLS,
    ProfileAnnotationNames.HAS_CANADA_VISA,
    ProfileAnnotationNames.HAS_INTERESTED_JOBS,
]

STAGE_CHOICES = [
    (ProfileAnnotationNames.HAS_PROFILE_INFORMATION, "Completed Profile"),
    (ProfileAnnotationNames.HAS_WORK_EXPERIENCE, "Work Experience"),
    (ProfileAnnotationNames.HAS_EDUCATION, "Education"),
    (ProfileAnnotationNames.HAS_CERTIFICATE, "Certificate"),
    (ProfileAnnotationNames.HAS_LANGUAGE_CERTIFICATE, "Language Certificate"),
    (ProfileAnnotationNames.HAS_SKILLS, "Skills"),
    (ProfileAnnotationNames.HAS_CANADA_VISA, "Canada Visa"),
]


def get_extended_blocklist():
    extended_blocklist = blocklist
    if (blocklist_path := Path(settings.BASE_DIR / "fixtures" / "blocklist_domains.json")).exists():
        with open(blocklist_path, "r") as f:
            extended_blocklist |= set(json.load(f))
    else:
        logger.warning("Blocklist fixture file not found")

    return extended_blocklist


ORGANIZATION_INVITATION_EXPIRY_DELTA = timedelta(days=1)

EXTENDED_EMAIL_BLOCKLIST = get_extended_blocklist()

EARLY_USERS_COUNT = 1000

ORGANIZATION_PHONE_OTP_CACHE_KEY = "organization-phone-otp-%(organization_id)s"
ORGANIZATION_PHONE_OTP_EXPIRY = 300
JOB_AVAILABLE_MIN_PERCENT_TRIGGER_THRESHOLD = 70
VERIFICATION_EMAIL_FROM = "verify@cpj.ai"
VERIFICATION_PHONE_FROM = "+1 (236) 501 4000"
SUPPORT_TICKET_SUBJECT_TEMPLATE = "Support Ticket Opened: %(ticket_id)s"
SUPPORT_EMAIL = "support@cpj.ai"
SUPPORT_RECIPIENT_LIST = [
    SUPPORT_EMAIL,
]


class VectorStores:
    JOB = CachableVectorStore(
        id="js-jobs-store",
        data_fn=partial(Job.objects.values, "pk", "title"),
        cache_key="jobs-store",
    )
    SKILL = CachableVectorStore(
        id="js-skills-store",
        data_fn=partial(Skill.objects.filter(insert_type=Skill.InsertType.SYSTEM).values, "pk", "title"),
        cache_key="skills-store",
    )
