import json
from collections import namedtuple

from celery import shared_task

from django.contrib.auth import get_user_model


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


@shared_task
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
