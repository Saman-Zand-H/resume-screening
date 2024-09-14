import traceback
from datetime import timedelta
from functools import wraps
from itertools import chain
from typing import Any, Callable, Dict, List, Protocol, Tuple

from config.settings.subscriptions import AccountSubscription
from flex_pubsub.tasks import register_task

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from notification.senders import send_notifications, NotificationContext
from notification.models import EmailNotification

from .utils import (
    extract_available_jobs,
    extract_certificate_text_content,
    extract_or_create_skills,
    extract_resume_json,
    get_user_additional_information,
)


from common.logging import get_logger

logger = get_logger()


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
def get_certificate_text(certificate_id: int) -> bool:
    from .models import (
        CertificateAndLicense,
        CertificateAndLicenseOfflineVerificationMethod,
    )

    if not (
        certificate_verification := CertificateAndLicenseOfflineVerificationMethod.objects.filter(
            **{CertificateAndLicenseOfflineVerificationMethod.certificate_and_license.field.name: certificate_id}
        ).first()
    ):
        raise ValueError(
            f"CertificateAndLicenseOfflineVerificationMethod with certificate_id {certificate_id} not found."
        )

    certificate_text = extract_certificate_text_content(certificate_verification.certificate_file.pk)
    CertificateAndLicense.objects.filter(pk=certificate_id).update(
        **{CertificateAndLicense.certificate_text.field.name: certificate_text.get("text_content", "")}
    )
    return True


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

    resume_json = extract_resume_json(resume.file.pk)

    if resume_json:
        Resume.objects.update_or_create(
            user=user,
            defaults={
                "resume_json": resume_json,
            },
        )
        return True


@register_task([AccountSubscription.EMAILING])
def send_email_async(recipient_list, from_email, subject, content, file_model_ids: List[int] = []):
    notifications = []
    recipient_list = list(recipient_list)  # Ensure it's a list
    for email in recipient_list:
        email_notification = EmailNotification(
            user=get_user_model().objects.get(email=email),
            title=subject,
            email=email,
            body=content,
        )
        notifications.append(
            NotificationContext(
                notification=email_notification,
                context={
                    "file_model_ids": file_model_ids,
                },
            )
        )
    send_notifications(*notifications, from_email=from_email)


def graphql_auth_async_email(func, args):
    func_name = func.__name__
    user = func.__self__.user

    user.status.send = patched_send_email
    func = getattr(user.status, func_name, None)
    if func:
        return func(*args)


def patched_send_email(subject, template, context, recipient_list=None):
    from graphql_auth.settings import graphql_auth_settings
    from django.template.loader import render_to_string
    from account.tasks import send_email_async

    _subject = render_to_string(subject, context).replace("\n", " ").strip()
    html_message = render_to_string(template, context)
    recipient_list = recipient_list or [getattr(context.get("user"), get_user_model().EMAIL_FIELD)]
    send_email_async.delay(
        recipient_list=recipient_list,
        from_email=graphql_auth_settings.EMAIL_FROM,
        content=html_message,
        subject=_subject,
    )
