from functools import partial, wraps
from typing import Any, Callable, Dict, List, Optional

from google.cloud.scheduler_v1.types.job import Job

from .app_settings import app_settings
from .scheduler import BaseSchedulerBackend
from .types import SchedulerJob
from .utils import are_subscriptions_valid


class TaskRegistry:
    def __init__(self) -> None:
        self.tasks: Dict[str, Callable] = {}
        self.schedule_configs: Dict[str, Job] = {}

    def register(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        raw_schedule: Optional[SchedulerJob] = None,
    ) -> Callable:
        if func is None:
            return lambda f: self.register(f, name=name, raw_schedule=raw_schedule)
        task_name = name or func.__name__
        self.tasks[task_name] = func
        if raw_schedule and (schedule := SchedulerJob.model_validate(raw_schedule)):
            self.schedule_configs[task_name] = schedule.model_dump()
            scheduler_backend: BaseSchedulerBackend = app_settings.SCHEDULER_BACKEND_CLASS()
            scheduler_backend.schedule(task_name, schedule)
        return func

    def _get_job_name(self, job: Job):
        return job.name.split("/")[-1]

    def sync_registered_jobs(self):
        scheduler_backend: BaseSchedulerBackend = app_settings.SCHEDULER_BACKEND_CLASS()
        jobs_list = scheduler_backend.list_jobs()
        unregistered_tasks = set(map(self._get_job_name, jobs_list.jobs)).difference(set(self.tasks))

        for task_name in unregistered_tasks:
            if self.schedule_configs.get(task_name):
                del self.schedule_configs[task_name]
            scheduler_backend.delete_job(task_name)

    def get_task(self, name: str) -> Optional[Callable]:
        return self.tasks.get(name)

    def get_schedule_config(self, name: str) -> Optional[Job]:
        return self.schedule_configs.get(name)

    def get_all_tasks(self) -> Dict[str, Callable]:
        return self.tasks


task_registry = TaskRegistry()


def register_task(
    subscriptions: List[str] = [],
    name: Optional[str] = None,
    schedule: Optional[SchedulerJob] = None,
) -> Callable[[Callable], Callable]:
    """
    Decorator to register a task.

    :param name: Optional custom name for the task.
    :param schedule: Optional schedule configuration dict.
    """

    def decorator(f: Callable) -> Callable:
        from .publisher import send_task

        task_name = name or f.__name__

        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        wrapper.delay = partial(send_task, task_name=task_name)
        wrapper.subscriptions = [subscription.value for subscription in subscriptions]
        if are_subscriptions_valid(subscriptions):
            task_registry.register(wrapper, name=task_name, raw_schedule=schedule)
        return wrapper

    return decorator
