import json
import os
import traceback
from collections import namedtuple
from datetime import timedelta
from functools import wraps
from itertools import chain
from logging import getLogger
from typing import Any, Callable, Dict, List, Protocol, Tuple

from config.settings.subscriptions import AccountSubscription
from flex_blob.builders import BlobResponseBuilder
from flex_blob.models import FileModel
from flex_pubsub.tasks import register_task

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.utils import timezone

from .utils import (
    extract_available_jobs,
    extract_or_create_skills,
    extract_resume_json,
    extract_resume_text,
    get_user_additional_information,
)

logger = getLogger("django")


@register_task([AccountSubscription.DOCUMENT_VERIFICATION], schedule={"schedule": "0 0 * * *"})
def self_verify_documents():
    from .models import DocumentAbstract, Education, WorkExperience

    self_verifiable_models: List[DocumentAbstract] = [WorkExperience, Education]

    for model in self_verifiable_models:
        model.objects.filter(
            status=DocumentAbstract.Status.SUBMITTED,
            updated_at__lte=timezone.now() - timedelta(days=7),
            allow_self_verification=True,
        ).update(status=DocumentAbstract.Status.SELF_VERIFIED)


class Task(Protocol):
    @classmethod
    def delay(cls, *args: Tuple[Any], **kwargs: Dict[str, Any]): ...


def user_task_decorator(func: Callable) -> Callable:
    task_name = func.__name__

    @wraps(func)
    def wrapper(*args: Tuple[Any], **kwargs: Dict[str, Any]):
        from .models import UserTask

        task_user_id = kwargs.pop("task_user_id", None)
        if not (user := get_user_model().objects.filter(pk=task_user_id).first()):
            logger.info(f"Running task {task_name}: user {task_user_id} not found.")
            (
                user_task := UserTask.objects.filter(user_id=task_user_id, task_name=task_name).first()
            ) and user_task.change_status(UserTask.Status.FAILED, "User not found.")
            return

        user_task = UserTask.objects.get_or_create(user=user, task_name=task_name)[0]
        if user_task.status == UserTask.Status.IN_PROGRESS:
            logger.info(f"Running task {task_name}: task {user_task.pk} is already in progress.")
            return

        user_task.change_status(UserTask.Status.IN_PROGRESS)
        try:
            func(*args, **kwargs)
            user_task.change_status(UserTask.Status.COMPLETED)
            return True
        except Exception as e:
            user_task.change_status(
                UserTask.Status.FAILED,
                f"{e}\n{traceback.format_exc()}",
            )

    return wrapper


def user_task_runner(task: Task, task_user_id: int, *args, **kwargs):
    from .models import UserTask

    task_name = task.name
    user_task, *_ = UserTask.objects.get_or_create(
        user_id=task_user_id,
        task_name=task_name,
    )

    if cache.get(cache_key := f"task_{task_name}_{task_user_id}_scheduled"):
        return

    if user_task.status not in [UserTask.Status.IN_PROGRESS, UserTask.Status.SCHEDULED]:
        user_task.change_status(UserTask.Status.SCHEDULED)
        cache.set(cache_key, (task, task_user_id, args, kwargs), timeout=5)
        task.delay(*args, task_user_id=task_user_id, **kwargs)


@register_task([AccountSubscription.ASSISTANTS])
@user_task_decorator
def find_available_jobs(user_id: int) -> bool:
    if not (user := get_user_model().objects.filter(pk=user_id).first()):
        raise ValueError(f"User with id {user_id} not found.")

    resume_json = {} if not hasattr(user, "resume") else user.resume.resume_json
    jobs = extract_available_jobs(resume_json, **get_user_additional_information(user_id))
    if not jobs:
        return

    user.profile.available_jobs.set(jobs)
    return True


@register_task([AccountSubscription.ASSISTANTS])
@user_task_decorator
def set_user_skills(user_id: int) -> bool:
    user = get_user_model().objects.get(pk=user_id)
    resume_json = {} if not hasattr(user, "resume") else user.resume.resume_json
    profile = user.profile

    extracted_skills = extract_or_create_skills(
        profile.raw_skills or [],
        resume_json,
        **get_user_additional_information(user_id),
    )

    profile.skills.clear() if not extracted_skills else profile.skills.set(chain.from_iterable(extracted_skills))
    return True


@register_task([AccountSubscription.ASSISTANTS])
@user_task_decorator
def set_user_resume_json(user_id: str) -> bool:
    from .models import Resume

    resume = Resume.objects.get(user_id=user_id)
    user = resume.user

    resume_text = extract_resume_text(resume.file.file.read())
    if not resume_text:
        raise ValueError("Resume text could not be extracted.")

    resume_json = extract_resume_json(resume_text)
    if resume_json:
        Resume.objects.update_or_create(
            user=user,
            defaults={
                "resume_json": resume_json,
                "text": resume_text,
            },
        )
        return True


class SerializableContext:
    def __init__(self, context):
        self._port = context.get_port()
        self._is_secure = context.is_secure()
        self._host = context.get_host()

    def get_port(self):
        return self._port

    def is_secure(self):
        return self._is_secure

    def get_host(self):
        return self._host

    def to_dict(self):
        return {
            "_port": self._port,
            "_is_secure": self._is_secure,
            "_host": self._host,
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls.__new__(cls)
        instance._port = data["_port"]
        instance._is_secure = data["_is_secure"]
        instance._host = data["_host"]
        return instance


@register_task([AccountSubscription.EMAILING])
def send_email_async(recipient_list, from_email, subject, content, file_model_ids: List[int] = []):
    email = EmailMessage(
        subject=subject,
        from_email=from_email,
        to=recipient_list,
        body=content,
    )
    email.content_subtype = "html"

    if file_model_ids:
        blob_builder = BlobResponseBuilder.get_response_builder()
        for file_model_id in file_model_ids:
            attachment = FileModel.objects.get(pk=file_model_id)
            file_name = os.path.basename(blob_builder.get_file_name(attachment))
            email.attach(
                file_name.split("/")[-1],
                attachment.file.read(),
                blob_builder.get_content_type(attachment),
            )

    email.send()


@register_task(subscriptions=[AccountSubscription.EMAILING])
def auth_async_email(func_name, user_email, context, arg):
    """
    Task to send an e-mail for the graphql_auth package
    """

    Info = namedtuple("info", ["context"])
    info = Info(context=SerializableContext.from_dict(json.loads(context)))

    user = get_user_model().objects.filter(email=user_email).select_related("status").first()

    if not user:
        raise ValueError(f"User with email {user_email} not found.")

    func = getattr(user.status, func_name, None)
    if not func:
        raise ValueError(f"Function {func_name} not found in user.status.")

    if arg is not None:
        return func(info, arg)
    return func(info)


def graphql_auth_async_email(func, args):
    func_name = func.__name__
    user_email = func.__self__.user.email
    info = args[0]
    arg = args[1] if len(args) == 2 else None

    serializable_context = SerializableContext(info.context)
    context = json.dumps(serializable_context.to_dict())

    auth_async_email.delay(func_name, user_email, context, arg)
