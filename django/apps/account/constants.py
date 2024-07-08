from functools import partial

from ai.types import CachableVectorStore
from common.models import Job, Skill
from disposable_email_domains import blocklist

EXTENDED_EMAIL_BLOCKLIST = blocklist.union(
    {
        "kisoq.com",
        "myweblaw.com",
    }
)

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
