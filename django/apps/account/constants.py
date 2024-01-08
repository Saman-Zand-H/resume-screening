from functools import partial

from ai.types import CachableVectorStore
from common.models import Job


class OpenAiAssistants:
    JOB = "asst_PuExhyoUGwAomIo5eCJJQWgr"


class VectorStores:
    JOB = CachableVectorStore(
        id="js-jobs-store",
        data_fn=partial(Job.objects.values, "pk", "title"),
        cache_key="jobs-store",
    )
