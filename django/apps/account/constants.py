from functools import partial

from ai.types import CachableVectorStore
from common.models import Job, Skill


class OpenAiAssistants:
    JOB = "asst_PuExhyoUGwAomIo5eCJJQWgr"
    SKILL = "asst_xgHHntfKpoAsnmQNeJntI4TH"


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
