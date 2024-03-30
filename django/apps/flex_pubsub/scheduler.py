import contextlib
import json
import logging

try:
    from google.api_core.exceptions import NotFound
    from google.cloud import scheduler_v1
    from google.cloud.scheduler_v1.types.cloudscheduler import (
        CreateJobRequest,
        DeleteJobRequest,
        GetJobRequest,
        ListJobsRequest,
        ListJobsResponse,
        UpdateJobRequest,
    )
    from google.cloud.scheduler_v1.types.job import Job
    from google.cloud.scheduler_v1.types.target import PubsubTarget
except ImportError:
    scheduler_v1 = None

from .app_settings import app_settings
from .types import SchedulerJob

logger = logging.getLogger("flex_pubsub")


class BaseSchedulerBackend:
    def delete_job(self, task_name: str) -> None:
        raise NotImplementedError

    def list_jobs(self) -> ListJobsResponse:
        raise NotImplementedError

    def schedule(self, task_name: str, schedule_config: SchedulerJob) -> Job:
        raise NotImplementedError


class LocalSchedulerBackend(BaseSchedulerBackend):
    def delete_job(self, task_name: str) -> None:
        logger.info(f"LocalSchedulerBackend: delete_job called with task_name={task_name}")

    def list_jobs(self) -> ListJobsResponse:
        logger.info("LocalSchedulerBackend: list_jobs called")
        return ListJobsResponse()

    def schedule(self, task_name: str, schedule_config: SchedulerJob) -> Job:
        logger.info(
            f"LocalSchedulerBackend: schedule called with task_name={task_name}, schedule_config={schedule_config}"
        )
        return Job(name=task_name)


class GoogleSchedulerBackend(BaseSchedulerBackend):
    def __init__(self) -> None:
        if scheduler_v1 is None:
            raise ImportError("google-cloud-scheduler is not installed.")
        credentials = app_settings.GOOGLE_CREDENTIALS
        self.client = scheduler_v1.CloudSchedulerClient(credentials=credentials)
        self.project_id = app_settings.GOOGLE_PROJECT_ID
        self.location = app_settings.SCHEDULER_LOCATION

        self.parent = self._get_parent()
        logger.info("Initialized GoogleSchedulerBackend")

    def delete_job(self, task_name: str) -> None:
        job_name = self._get_job_name(task_name)
        self.client.delete_job(request=DeleteJobRequest(name=job_name))

    def list_jobs(self) -> ListJobsResponse:
        return self.client.list_jobs(request=ListJobsRequest(parent=self.parent))

    def schedule(self, task_name: str, schedule_config: SchedulerJob) -> Job:
        job = Job(
            name=self._get_job_name(task_name),
            schedule=schedule_config.schedule,
            time_zone=schedule_config.time_zone,
            pubsub_target=PubsubTarget(
                topic_name=app_settings.TOPIC_PATH,
                data=json.dumps(
                    {
                        "task_name": task_name,
                        "args": schedule_config.args,
                        "kwargs": schedule_config.kwargs,
                    }
                ).encode(),
            ),
        )
        return self._get_or_create_or_update_task(job)

    def _get_job_name(self, task_name: str) -> str:
        return f"{self.parent}/jobs/{task_name}"

    def _get_parent(self):
        return f"projects/{self.project_id}/locations/{self.location}"

    def _get_job(self, request: GetJobRequest) -> Job | None:
        with contextlib.suppress(NotFound):
            return self.client.get_job(request=request)

    def _compare_jobs(self, retrieved_job: Job, job: Job) -> bool:
        return (
            retrieved_job.schedule == job.schedule
            and retrieved_job.time_zone == job.time_zone
            and retrieved_job.pubsub_target == job.pubsub_target
        )

    def _get_or_create_or_update_task(self, job: Job) -> Job:
        if retrieved_job := self._get_job(GetJobRequest(name=job.name)):
            if not self._compare_jobs(retrieved_job, job):
                return self.client.update_job(request=UpdateJobRequest(job=job))
            return retrieved_job

        return self.client.create_job(request=CreateJobRequest(parent=self.parent, job=job))
