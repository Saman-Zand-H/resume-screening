from functools import partial

from ai.types import CachableVectorStore
from common.models import Job, Skill
from config.settings.constants import Assistants

from django.conf import settings

JOB_AVAILABLE_MIN_PERCENT_TRIGGER_THRESHOLD = 70
VERIFICATION_EMAIL_FROM = "verify@cpj.ai"
VERIFICATION_PHONE_FROM = "+1 (236) 501 4000"
SUPPORT_TICKET_SUBJECT_TEMPLATE = "Support Ticket Opened: %(ticket_id)s"
SUPPORT_EMAIL = "support@cpj.ai"
SUPPORT_RECIPIENT_LIST = [
    SUPPORT_EMAIL,
]


class OpenAiAssistants:
    JOB = settings.ASSISTANT_IDS.get(Assistants.JOB) or "asst_PuExhyoUGwAomIo5eCJJQWgr"
    SKILL = settings.ASSISTANT_IDS.get(Assistants.SKILL) or "asst_xgHHntfKpoAsnmQNeJntI4TH"
    RESUME = settings.ASSISTANT_IDS.get(Assistants.RESUME) or "asst_myiZIH7CBPn4ciVbqDGMF8ZL"
    HEADLINES = settings.ASSISTANT_IDS.get(Assistants.HEADLINES) or "asst_hhsL57Pbb95cNuzrVImCvGWR"
    GENERATE_RESUME = settings.ASSISTANT_IDS.get(Assistants.GENERATE_RESUME) or "asst_VXIB9igMMv7Fj4EElfygf6FD"


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
