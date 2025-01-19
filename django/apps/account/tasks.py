import os
import traceback
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Protocol, Tuple

from common.logging import get_logger
from common.utils import fj
from config.settings.subscriptions import AccountSubscription
from flex_blob.builders import BlobResponseBuilder
from flex_blob.models import FileModel
from flex_pubsub.tasks import register_task
from func_timeout import FunctionTimedOut, func_timeout
from graphql_jwt.refresh_token.models import RefreshToken as UserRefreshToken
from notification.models import EmailNotification
from notification.senders import NotificationContext, send_notifications

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.db.models.lookups import In, IsNull, LessThanOrEqual
from django.utils import timezone

from .typing import ResumeJson
from .utils import (
    extract_certificate_text_content,
    extract_resume_json,
    set_contacts_from_resume_json,
    set_profile_from_resume_json,
)

logger = get_logger()


@register_task([AccountSubscription.DAILY_EXECUTION], schedule={"schedule": "0 0 * * *"})
def self_verify_documents():
    from .models import DocumentAbstract, Education, WorkExperience

    self_verifiable_models: List[DocumentAbstract] = [WorkExperience, Education]

    for model in self_verifiable_models:
        model.objects.filter(
            **{
                fj(model.status): DocumentAbstract.Status.SUBMITTED,
                fj(model.updated_at, LessThanOrEqual.lookup_name): timezone.now() - timedelta(days=7),
                fj(model.allow_self_verification): True,
            }
        ).update(**{fj(model.status): DocumentAbstract.Status.SELF_VERIFIED})


@register_task([AccountSubscription.DAILY_EXECUTION], schedule={"schedule": "0 0 * * *"})
def set_expiry():
    from .models import OrganizationJobPosition

    OrganizationJobPosition.set_expiry()


@register_task([AccountSubscription.DAILY_EXECUTION], schedule={"schedule": "*/30 * * * *"})
def clean_revoked_tokens():
    (
        UserRefreshToken.objects.expired().filter(expired=True)
        | UserRefreshToken.objects.filter(**{fj(UserRefreshToken.revoked, IsNull.lookup_name): False})
    ).delete()


class Task(Protocol):
    @classmethod
    def delay(cls, *args: Tuple[Any], **kwargs: Dict[str, Any]): ...


def user_task_decorator(timeout_seconds: int) -> Callable:
    def wrapper(func: Callable):
        task_name = func.__name__

        @wraps(func)
        def inner_wrapper(*args: Tuple[Any], **kwargs: Dict[str, Any]):
            from .models import User, UserTask

            task_user_id = kwargs.pop("task_user_id", None)
            if not (user := get_user_model().objects.filter(**{User._meta.pk.attname: task_user_id}).first()):
                logger.info(f"Running task {task_name}: user {task_user_id} not found.")
                (
                    user_task := UserTask.objects.filter(
                        **{UserTask.user.field.attname: task_user_id, fj(UserTask.task_name): task_name}
                    ).latest(UserTask.created)
                ) and user_task.change_status(UserTask.Status.FAILED, "User not found.")
                return

            user_task = UserTask.objects.filter(
                **{
                    fj(UserTask.status, In.lookup_name): [
                        UserTask.Status.IN_PROGRESS,
                        UserTask.Status.SCHEDULED,
                    ]
                }
            ).get_or_create(user=user, task_name=task_name)[0]
            if user_task.status == UserTask.Status.IN_PROGRESS:
                logger.info(f"Running task {task_name}: task {user_task.pk} is already in progress.")
                return

            user_task.change_status(UserTask.Status.IN_PROGRESS)

            try:
                func_timeout(timeout_seconds, func, args=args, kwargs=kwargs)
                user_task.change_status(UserTask.Status.COMPLETED)

            except FunctionTimedOut:
                user_task.change_status(
                    UserTask.Status.TIMEDOUT,
                    f"Timeout after {timeout_seconds} seconds.\n{traceback.format_exc()}",
                )

            except Exception as e:
                user_task.change_status(
                    UserTask.Status.FAILED,
                    f"{e}\n{traceback.format_exc()}",
                )

        return inner_wrapper

    return wrapper


def user_task_runner(task: Task, task_user_id: int, *args, **kwargs):
    from .models import UserTask

    task_name = task.name
    user_task, *_ = UserTask.objects.filter(
        **{
            fj(UserTask.status, In.lookup_name): [
                UserTask.Status.IN_PROGRESS,
                UserTask.Status.SCHEDULED,
            ],
        }
    ).get_or_create(
        user_id=task_user_id,
        task_name=task_name,
    )

    if cache.get(cache_key := f"task_{task_name}_{task_user_id}_scheduled"):
        return

    if user_task.status not in [UserTask.Status.IN_PROGRESS, UserTask.Status.SCHEDULED]:
        cache.set(cache_key, (task, task_user_id, args, kwargs), timeout=5)
        task.delay(*args, task_user_id=task_user_id, **kwargs)
        user_task.change_status(UserTask.Status.SCHEDULED)


@register_task([AccountSubscription.ASSISTANTS])
@user_task_decorator(timeout_seconds=120)
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
    CertificateAndLicense.objects.filter(**{CertificateAndLicense.pk.attname: certificate_id}).update(
        **{CertificateAndLicense.certificate_text.field.name: certificate_text.get("text_content", "")}
    )
    return True


def set_user_resume_json(user_id: str) -> bool:
    from .models import Resume

    resume = Resume.objects.get(user_id=user_id)
    user = resume.user

    if not ((resume_json := extract_resume_json(resume.file.pk)) and ResumeJson.model_validate(resume_json)):
        return

    Resume.objects.update_or_create(user=user, defaults={"resume_json": resume_json})

    set_contacts_from_resume_json(user, resume_json)
    set_profile_from_resume_json(user, resume_json)

    return True


@register_task([AccountSubscription.EMAILING])
def send_email_async_non_existing_user(recipient_list, from_email, subject, content, file_model_ids: List[int] = []):
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


@register_task([AccountSubscription.EMAILING])
def send_email_async(recipient_list, from_email, subject, content, file_model_ids: List[int] = []):
    notifications = []
    recipient_list = list(recipient_list)  # Ensure it's a list
    for email in recipient_list:
        try:
            email_notification = EmailNotification(
                user=get_user_model().objects.get(email=email),
                title=subject,
                email=email,
                body=content,
            )
        except get_user_model().DoesNotExist:
            send_email_async_non_existing_user(recipient_list, from_email, subject, content, file_model_ids)
            continue
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

    from account.tasks import send_email_async
    from django.template.loader import render_to_string

    _subject = render_to_string(subject, context).replace("\n", " ").strip()
    html_message = render_to_string(template, context)
    recipient_list = recipient_list or [getattr(context.get("user"), get_user_model().EMAIL_FIELD)]
    send_email_async.delay(
        recipient_list=recipient_list,
        from_email=graphql_auth_settings.EMAIL_FROM,
        content=html_message,
        subject=_subject,
    )
