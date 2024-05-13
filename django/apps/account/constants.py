from functools import partial

from ai.types import CachableVectorStore
from common.models import Job, Skill
from config.settings.constants import Assistants

from django.conf import settings

USER_TASKS_TIMEOUT_SECONDS = 60 * 5  # 5 minutes
JOB_AVAILABLE_MIN_SCORE_TRIGGER_THRESHOLD = 80


class OpenAiAssistants:
    JOB = settings.ASSISTANT_IDS.get(Assistants.JOB) or "asst_PuExhyoUGwAomIo5eCJJQWgr"
    SKILL = settings.ASSISTANT_IDS.get(Assistants.SKILL) or "asst_xgHHntfKpoAsnmQNeJntI4TH"
    RESUME = settings.ASSISTANT_IDS.get(Assistants.RESUME) or "asst_myiZIH7CBPn4ciVbqDGMF8ZL"
    HEADLINES = settings.ASSISTANT_IDS.get(Assistants.HEADLINES) or "asst_hhsL57Pbb95cNuzrVImCvGWR"


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
