from flex_pubsub.tasks import task_registry

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class GenderChoices(TextChoices):
    MALE = "male", _("Male")
    FEMALE = "female", _("Female")
    NOT_KNOWN = "not_known", _("Not Known")
    NOT_APPLICABLE = "not_applicable", _("Not Applicable")


class ContactType(TextChoices):
    WEBSITE = "website", _("Website")
    ADDRESS = "address", _("Address")
    LINKEDIN = "linkedin", _("LinkedIn")
    WHATSAPP = "whatsapp", _("WhatsApp")
    PHONE = "phone", _("Phone")


class IEEEvaluator(TextChoices):
    WES = "wes", _("World Education Services")
    IQAS = "iqas", _("International Qualifications Assessment Service")
    ICAS = "icas", _("International Credential Assessment Service of Canada")
    CES = "ces", _("Comparative Education Service")
    OTHER = "other", _("Other")


class WorkExperienceGrade(TextChoices):
    INTERN = "intern", _("Intern")
    ASSOCIATE = "associate", _("Associate")
    JUNIOR = "junior", _("Junior")
    MID_LEVEL = "mid_level", _("Mid-Level")
    SENIOR = "senior", _("Senior")
    MANAGER = "manager", _("Manager")
    DIRECTOR = "director", _("Director")
    CTO = "cto", _("CTO")
    CFO = "cfo", _("CFO")
    CEO = "ceo", _("CEO")


class EducationDegree(TextChoices):
    BACHELORS = "bachelors", _("Bachelors")
    MASTERS = "masters", _("Masters")
    PHD = "phd", _("PhD")
    ASSOCIATE = "associate", _("Associate")
    DIPLOMA = "diploma", _("Diploma")
    CERTIFICATE = "certificate", _("Certificate")


class UserTaskStatus(TextChoices):
    SCHEDULED = "scheduled", _("Scheduled")
    IN_PROGRESS = "in_progress", _("In Progress")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")
    TIMEDOUT = "timedout", _("Timed-Out")


class DefaultRoles(TextChoices):
    OWNER = "owner", "Owner"


def get_task_names_choices():
    return [(i, i) for i in task_registry.get_all_tasks()]
