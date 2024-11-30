from typing import NamedTuple

from account.constants import ProfileAnnotationNames
from account.models import Profile, User
from cities_light.models import City, Country
from common.populators import BasePopulator
from common.utils import fj
from flex_report.models import Column, Template, TemplateSavedFilter

from django.contrib.contenttypes.models import ContentType
from django.db.models.lookups import Exact
from django.template.loader import render_to_string

from .constants import NotificationTypes
from .models import (
    Campaign,
    CampaignNotificationType,
    NotificationTemplate,
)


class SavedFilterNames:
    RESUME_UPLOADED_NO_INFORMATION = "Resume Uploaded, No Info Completed"
    DEGREE_UPLOADED_NOT_VERIFIED = "Degree Uploaded, Not Verified"
    NO_WORK_EXPERIENCE = "No Work Experience"
    NO_CERTIFICATE = "No Certificate"
    NO_LANGUAGE_CERTIFICATE = "No Language Certificate"
    NO_VISA_STATUS = "No Visa Status"
    NO_JOB_INTEREST = "No Job Interest"


FILTER_TEMPLATE_MAPPER = {
    SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION: {
        "body": "notification/populators/resume_uploaded_no_information.html",
        "subject": "Complete CPJ Profile",
    },
    SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED: {
        "body": "notification/populators/degree_uploaded_not_verified.html",
        "subject": "Verify Educations on CPJ",
    },
    SavedFilterNames.NO_WORK_EXPERIENCE: {
        "body": "notification/populators/no_work_experience.html",
        "subject": "Work Experiences on CPJ",
    },
    SavedFilterNames.NO_CERTIFICATE: {
        "body": "notification/populators/no_certificate.html",
        "subject": "Certificates on CPJ",
    },
    SavedFilterNames.NO_LANGUAGE_CERTIFICATE: {
        "body": "notification/populators/no_language_certificate.html",
        "subject": "Language Certificates on CPJ",
    },
    SavedFilterNames.NO_VISA_STATUS: {
        "body": "notification/populators/no_canada_visa.html",
        "subject": "Canada Visa on CPJ",
    },
    SavedFilterNames.NO_JOB_INTEREST: {
        "body": "notification/populators/no_job_interest.html",
        "subject": "Job Interests on CPJ",
    },
}


class UpsertInfo(NamedTuple):
    data: dict
    defaults: dict = {}


class NotificationPopulator(BasePopulator):
    def populate_template(self):
        profile_content_type = ContentType.objects.get_for_model(Profile)

        template = Template.objects.update_or_create(
            **{
                fj(Template.model): profile_content_type,
                fj(Template.filters): {},
            },
            defaults={
                fj(Template.title): "Profiles",
                fj(Template.status): Template.Status.complete,
            },
        )[0]

        columns_data = [
            UpsertInfo(
                data={
                    fj(Column.title): fj(Profile.user, User.first_name),
                    fj(Column.model): profile_content_type,
                }
            ),
            UpsertInfo(
                data={
                    fj(Column.title): fj(Profile.user, User.last_name),
                    fj(Column.model): profile_content_type,
                }
            ),
            UpsertInfo(
                data={
                    fj(Column.title): fj(Profile.user, User.email),
                    fj(Column.model): profile_content_type,
                }
            ),
            UpsertInfo(
                data={
                    fj(Column.title): fj(Profile.user, User.date_joined),
                    fj(Column.model): profile_content_type,
                }
            ),
            UpsertInfo(
                data={
                    fj(Column.title): fj(Profile.user, User.last_login),
                    fj(Column.model): profile_content_type,
                }
            ),
            UpsertInfo(
                data={
                    fj(Column.title): ProfileAnnotationNames.HAS_RESUME,
                    fj(Column.model): profile_content_type,
                }
            ),
            UpsertInfo(
                data={
                    fj(Column.title): ProfileAnnotationNames.STAGE_DATA,
                    fj(Column.model): profile_content_type,
                }
            ),
            UpsertInfo(
                data={
                    fj(Column.title): ProfileAnnotationNames.AGE,
                    fj(Column.model): profile_content_type,
                }
            ),
            UpsertInfo(
                data={
                    fj(Column.title): fj(Profile.city, City.country, Country.name),
                    fj(Column.model): profile_content_type,
                }
            ),
        ]

        columns = []
        for column_data in columns_data:
            columns.append(Column.objects.update_or_create(**column_data.data, defaults=column_data.defaults)[0])

        template.columns.add(*columns)
        return template

    def populate_filters(self):
        template = self.populate_template()

        filters_data = {
            SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION: UpsertInfo(
                defaults={
                    fj(TemplateSavedFilter.template): template,
                    fj(TemplateSavedFilter.filters): {
                        fj(ProfileAnnotationNames.HAS_RESUME, Exact.lookup_name): True,
                        fj(ProfileAnnotationNames.HAS_PROFILE_INFORMATION, Exact.lookup_name): False,
                    },
                },
                data={
                    fj(TemplateSavedFilter.title): SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION,
                },
            ),
            SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED: UpsertInfo(
                defaults={
                    fj(TemplateSavedFilter.template): template,
                    fj(TemplateSavedFilter.filters): {
                        fj(ProfileAnnotationNames.HAS_EDUCATION, Exact.lookup_name): True,
                        fj(ProfileAnnotationNames.HAS_UNVERIFIED_EDUCATION, Exact.lookup_name): True,
                    },
                },
                data={
                    fj(TemplateSavedFilter.title): SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED,
                },
            ),
            SavedFilterNames.NO_WORK_EXPERIENCE: UpsertInfo(
                defaults={
                    fj(TemplateSavedFilter.template): template,
                    fj(TemplateSavedFilter.filters): {
                        fj(ProfileAnnotationNames.HAS_WORK_EXPERIENCE, Exact.lookup_name): False,
                    },
                },
                data={
                    fj(TemplateSavedFilter.title): SavedFilterNames.NO_WORK_EXPERIENCE,
                },
            ),
            SavedFilterNames.NO_CERTIFICATE: UpsertInfo(
                defaults={
                    fj(TemplateSavedFilter.template): template,
                    fj(TemplateSavedFilter.filters): {
                        fj(ProfileAnnotationNames.HAS_CERTIFICATE, Exact.lookup_name): False,
                    },
                },
                data={
                    fj(TemplateSavedFilter.title): SavedFilterNames.NO_CERTIFICATE,
                },
            ),
            SavedFilterNames.NO_LANGUAGE_CERTIFICATE: UpsertInfo(
                defaults={
                    fj(TemplateSavedFilter.template): template,
                    fj(TemplateSavedFilter.filters): {
                        fj(ProfileAnnotationNames.HAS_LANGUAGE_CERTIFICATE, Exact.lookup_name): False,
                    },
                },
                data={
                    fj(TemplateSavedFilter.title): SavedFilterNames.NO_LANGUAGE_CERTIFICATE,
                },
            ),
            SavedFilterNames.NO_VISA_STATUS: UpsertInfo(
                defaults={
                    fj(TemplateSavedFilter.template): template,
                    fj(TemplateSavedFilter.filters): {
                        fj(ProfileAnnotationNames.HAS_CANADA_VISA, Exact.lookup_name): False,
                    },
                },
                data={
                    fj(TemplateSavedFilter.title): SavedFilterNames.NO_VISA_STATUS,
                },
            ),
            SavedFilterNames.NO_JOB_INTEREST: UpsertInfo(
                data={
                    fj(TemplateSavedFilter.title): SavedFilterNames.NO_JOB_INTEREST,
                },
                defaults={
                    fj(TemplateSavedFilter.filters): {
                        fj(ProfileAnnotationNames.HAS_INTERESTED_JOBS, Exact.lookup_name): False,
                    },
                    fj(TemplateSavedFilter.template): template,
                },
            ),
        }

        filters = {}
        for filter_key, filter_upsert_data in filters_data.items():
            filters[filter_key] = TemplateSavedFilter.objects.update_or_create(
                **filter_upsert_data.data,
                defaults=filter_upsert_data.defaults,
            )[0]

        return filters

    def populate_campaigns(self):
        filters = self.populate_filters()

        campaigns_data = {
            SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION: UpsertInfo(
                data={
                    fj(Campaign.saved_filter): filters.get(SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION),
                },
                defaults={
                    fj(Campaign.title): SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION,
                    fj(Campaign.crontab): "0 0 */3 * *",
                    fj(Campaign.max_attempts): 3,
                },
            ),
            SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED: UpsertInfo(
                data={
                    fj(Campaign.saved_filter): filters.get(SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED),
                },
                defaults={
                    fj(Campaign.title): SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED,
                    fj(Campaign.crontab): "0 0 */4 * *",
                    fj(Campaign.max_attempts): 3,
                },
            ),
            SavedFilterNames.NO_WORK_EXPERIENCE: UpsertInfo(
                data={
                    fj(Campaign.saved_filter): filters.get(SavedFilterNames.NO_WORK_EXPERIENCE),
                },
                defaults={
                    fj(Campaign.title): SavedFilterNames.NO_WORK_EXPERIENCE,
                    fj(Campaign.crontab): "0 0 */5 * *",
                    fj(Campaign.max_attempts): 3,
                },
            ),
            SavedFilterNames.NO_CERTIFICATE: UpsertInfo(
                data={
                    fj(Campaign.saved_filter): filters.get(SavedFilterNames.NO_CERTIFICATE),
                },
                defaults={
                    fj(Campaign.title): SavedFilterNames.NO_CERTIFICATE,
                    fj(Campaign.crontab): "0 0 */6 * *",
                    fj(Campaign.max_attempts): 3,
                },
            ),
            SavedFilterNames.NO_LANGUAGE_CERTIFICATE: UpsertInfo(
                data={
                    fj(Campaign.saved_filter): filters.get(SavedFilterNames.NO_LANGUAGE_CERTIFICATE),
                },
                defaults={
                    fj(Campaign.title): SavedFilterNames.NO_LANGUAGE_CERTIFICATE,
                    fj(Campaign.crontab): "0 0 */7 * *",
                    fj(Campaign.max_attempts): 3,
                },
            ),
            SavedFilterNames.NO_VISA_STATUS: UpsertInfo(
                data={
                    fj(Campaign.saved_filter): filters.get(SavedFilterNames.NO_VISA_STATUS),
                },
                defaults={
                    fj(Campaign.title): SavedFilterNames.NO_VISA_STATUS,
                    fj(Campaign.crontab): "0 0 */3 * *",
                    fj(Campaign.max_attempts): 3,
                },
            ),
            SavedFilterNames.NO_JOB_INTEREST: UpsertInfo(
                data={
                    fj(Campaign.saved_filter): filters.get(SavedFilterNames.NO_JOB_INTEREST),
                },
                defaults={
                    fj(Campaign.title): SavedFilterNames.NO_JOB_INTEREST,
                    fj(Campaign.crontab): "0 0 */4 * *",
                    fj(Campaign.max_attempts): 3,
                },
            ),
        }

        campaigns = {}
        for campaign_key, campaign_data in campaigns_data.items():
            campaigns[campaign_key] = Campaign.objects.update_or_create(
                **campaign_data.data,
                defaults=campaign_data.defaults,
            )[0]

        notification_template_data = {
            campaign_title: {
                "body": UpsertInfo(
                    data={
                        fj(NotificationTemplate.title): f"{campaign_title} Body",
                    },
                    defaults={
                        fj(NotificationTemplate.content_template): render_to_string(
                            template_name=FILTER_TEMPLATE_MAPPER[campaign_title]["body"]
                        ),
                    },
                ),
                "subject": UpsertInfo(
                    data={
                        fj(NotificationTemplate.title): f"{campaign_title} Subject",
                    },
                    defaults={
                        fj(NotificationTemplate.content_template): FILTER_TEMPLATE_MAPPER[campaign_title]["subject"]
                    },
                ),
            }
            for campaign_title in FILTER_TEMPLATE_MAPPER
        }

        templates = {}
        for template_key, template_data in notification_template_data.items():
            templates[template_key] = {}
            templates[template_key]["body"] = NotificationTemplate.objects.update_or_create(
                **template_data["body"].data,
                defaults=template_data["body"].defaults,
            )[0]
            templates[template_key]["subject"] = NotificationTemplate.objects.update_or_create(
                **template_data["subject"].data,
                defaults=template_data["subject"].defaults,
            )[0]

        campaign_notification_type_data = [
            UpsertInfo(
                data={
                    fj(CampaignNotificationType.campaign): campaign,
                    fj(CampaignNotificationType.notification_type): notification_type,
                },
                defaults={
                    CampaignNotificationType.body.field.name: templates[campaign_title]["body"],
                    CampaignNotificationType.subject.field.name: templates[campaign_title]["subject"],
                },
            )
            for campaign_title, campaign in campaigns.items()
            for notification_type, _ in NotificationTypes.choices
        ]

        for campaign_notification_type in campaign_notification_type_data:
            CampaignNotificationType.objects.update_or_create(
                **campaign_notification_type.data,
                defaults=campaign_notification_type.defaults,
            )

    def populate(self):
        self.populate_campaigns()
