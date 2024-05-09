import json
from collections import namedtuple

from account.models import Resume, User
from config.settings.subscriptions import AccountSubscription
from flex_pubsub.tasks import register_task

from django.contrib.auth import get_user_model

from .models import UserTask
from .utils import (
    extract_available_jobs,
    extract_or_create_skills,
    extract_resume_headlines,
    extract_resume_json,
    extract_resume_text,
)


@register_task([AccountSubscription.ASSISTANTS])
def find_available_jobs(user_id: int) -> bool:
    if not (user := get_user_model().objects.filter(pk=user_id).first()):
        return False

    user_task = UserTask.objects.get_or_create(user=user, task_name=find_available_jobs.__name__)[0]
    if user_task.status == UserTask.TaskStatus.IN_PROGRESS:
        return False

    user_task.change_status(UserTask.TaskStatus.IN_PROGRESS)
    resume_json = {} if not hasattr(user, "resume") else user.resume.resume_json
    jobs = extract_available_jobs(resume_json)
    if jobs:
        user.available_jobs.set(jobs)
        user_task.change_status(UserTask.TaskStatus.COMPLETED)
        return True

    user_task.change_status(UserTask.TaskStatus.FAILED)
    return False


@register_task([AccountSubscription.ASSISTANTS])
def set_user_skills(user_pk: int) -> bool:
    user = User.objects.get(pk=user_pk)
    user_task = UserTask.objects.get_or_create(user=user, task_name=set_user_skills.__name__)[0]
    if user_task.status == UserTask.TaskStatus.IN_PROGRESS:
        return False

    user_task.change_status(UserTask.TaskStatus.IN_PROGRESS)
    resume_json = {} if not hasattr(user, "resume") else user.resume.resume_json
    extracted_skills = extract_or_create_skills(user.raw_skills or [], resume_json)
    if not extracted_skills:
        user_task.change_status(UserTask.TaskStatus.FAILED)
        return False
    if extracted_skills:
        user.skills.set(extracted_skills)
        user_task.change_status(UserTask.TaskStatus.COMPLETED)
        return True

    user_task.change_status(UserTask.TaskStatus.FAILED)
    return False


@register_task([AccountSubscription.ASSISTANTS])
def set_user_resume_json(resume_file: bytes, user_id: int) -> bool:
    user = User.objects.get(pk=user_id)
    user_task = UserTask.objects.get_or_create(user=user, task_name=set_user_resume_json.__name__)[0]
    if user_task.status == UserTask.TaskStatus.IN_PROGRESS:
        return False

    resume_text = extract_resume_text(resume_file)
    if not resume_text:
        user_task.change_status(UserTask.TaskStatus.FAILED)
        return False

    user_task.change_status(UserTask.TaskStatus.IN_PROGRESS)
    try:
        resume_json = extract_resume_json(resume_text)
        if resume_json:
            resume_headlines = extract_resume_headlines(resume_json)
            Resume.objects.update_or_create(
                user=user,
                defaults={
                    "resume_json": resume_json.model_dump(),
                    "text": resume_text,
                    "headline": resume_headlines.headline,
                    "about_me": resume_headlines.about_me,
                },
            )
            find_available_jobs.delay(user.pk)
            user_task.change_status(UserTask.TaskStatus.COMPLETED)
            return True
    except Exception:
        user_task.change_status(UserTask.TaskStatus.FAILED)
        return False


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


@register_task(subscriptions=[AccountSubscription.EMAILING])
def async_email(func_name, user_email, context, arg):
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

    async_email.delay(func_name, user_email, context, arg)
