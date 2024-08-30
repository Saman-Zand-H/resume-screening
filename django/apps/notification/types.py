from typing import Any, Callable, Dict, List, Literal, NamedTuple, TypedDict, Union

from django.db.models import Model

from .constants import NotificationTypes

NotificationType = Literal[
    NotificationTypes.EMAIL,
    NotificationTypes.SMS,
    NotificationTypes.PUSH,
    NotificationTypes.IN_APP,
]


class MapperKey(NamedTuple):
    model: Model
    notification_type: NotificationType


class BaseMappedReport(TypedDict):
    user_id: int
    context: Dict[str, Any]


class EmailNotification(BaseMappedReport):
    email: str


class SMSNotification(BaseMappedReport):
    phone_numbers: List[str]


class PushNotification(BaseMappedReport):
    device_ids: List[int]


class InAppNotification(BaseMappedReport):
    pass


MapperReport = Union[
    EmailNotification,
    SMSNotification,
    PushNotification,
    InAppNotification,
]

ReportMapperType = Callable[[Model], List[BaseMappedReport]]
