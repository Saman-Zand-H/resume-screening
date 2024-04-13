import json
from collections import namedtuple

from account.models import Resume, User
from flex_pubsub.tasks import register_task

from django.contrib.auth import get_user_model

from .subscriptions import AccountSubscription
from .utils import extract_available_jobs, extract_or_create_skills


def find_available_jobs(resume_pk: int) -> bool:
    resume = Resume.objects.get(pk=resume_pk)
    resume_text = resume.get_or_set_resume_text()
    jobs = extract_available_jobs(resume_text)
    if jobs:
        resume.user.available_jobs.set(jobs)
        return True
    return False


def set_user_skills(user_pk: int) -> bool:
    user = User.objects.get(pk=user_pk)
    extracted_skills = extract_or_create_skills(user.raw_skills)
    if not extracted_skills:
        return False
    existing_skills = extracted_skills[0]
    if existing_skills:
        user.skills.set(existing_skills)
        return True
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
    context = (json.dumps(serializable_context.to_dict()),)

    async_email.delay(func_name, user_email, context[0], arg)
