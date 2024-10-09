from itertools import chain

from account.constants import ProfileAnnotationNames
from account.models import Profile, User
from common.populators import BasePopulator
from common.utils import fields_join
from flex_report.models import Column, Template, TemplateSavedFilter

from django.contrib.contenttypes.models import ContentType
from django.db.models.functions.datetime import TruncDate
from django.db.models.lookups import In
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
        "body": "notification/resume_uploaded_no_information.html",
        "subject": "Complete CPJ Profile",
    },
    SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED: {
        "body": "notification/degree_uploaded_not_verified.html",
        "subject": "Verify Educations on CPJ",
    },
    SavedFilterNames.NO_WORK_EXPERIENCE: {
        "body": "notification/no_work_experience.html",
        "subject": "Work Experiences on CPJ",
    },
    SavedFilterNames.NO_CERTIFICATE: {
        "body": "notification/no_certificate.html",
        "subject": "Certificates on CPJ",
    },
    SavedFilterNames.NO_LANGUAGE_CERTIFICATE: {
        "body": "notification/no_language_certificate.html",
        "subject": "Language Certificates on CPJ",
    },
    SavedFilterNames.NO_VISA_STATUS: {
        "body": "notification/no_canada_visa.html",
        "subject": "Canada Visa on CPJ",
    },
    SavedFilterNames.NO_JOB_INTEREST: {
        "body": "notification/no_job_interest.html",
        "subject": "Job Interests on CPJ",
    },
}


class Populator(BasePopulator):
    def populate_template(self):
        profile_content_type = ContentType.objects.get_for_model(Profile)
        template_data = Template(
            **{
                fields_join(Template.title): "Profiles",
                fields_join(Template.model): profile_content_type,
                fields_join(Template.status): Template.Status.complete,
            }
        )
        template = Template.objects.bulk_create(
            [template_data],
            ignore_conflicts=True,
            unique_fields=[fields_join(Template.model), fields_join(Template.filters)],
        )[0]
        columns_data = [
            Column(
                **{
                    fields_join(Column.title): fields_join(Profile.user, User.first_name),
                    fields_join(Column.model): profile_content_type,
                },
            ),
            Column(
                **{
                    fields_join(Column.title): fields_join(Profile.user, User.last_name),
                    fields_join(Column.model): profile_content_type,
                },
            ),
            Column(
                **{
                    fields_join(Column.title): fields_join(Profile.user, User.email),
                    fields_join(Column.model): profile_content_type,
                },
            ),
            Column(
                **{
                    fields_join(Column.title): fields_join(Profile.gender),
                    fields_join(Column.model): profile_content_type,
                },
            ),
            Column(
                **{
                    fields_join(Column.title): fields_join(Profile.user, User.date_joined, TruncDate.lookup_name),
                    fields_join(Column.model): profile_content_type,
                },
            ),
            Column(
                **{
                    fields_join(Column.title): fields_join(Profile.user, User.last_login, TruncDate.lookup_name),
                    fields_join(Column.model): profile_content_type,
                },
            ),
        ]

        columns = Column.objects.bulk_create(columns_data, ignore_conflicts=True)

        template.columns.add(*columns)
        return template

    def populate_filters(self):
        template = self.populate_template()

        filters_data = {
            SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION: TemplateSavedFilter(
                **{
                    fields_join(TemplateSavedFilter.title): SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION,
                    fields_join(TemplateSavedFilter.template): template,
                    fields_join(TemplateSavedFilter.filters): {
                        fields_join(ProfileAnnotationNames.HAS_RESUME): True,
                        fields_join(ProfileAnnotationNames.HAS_INCOMPLETE_STAGES): True,
                    },
                }
            ),
            SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED: TemplateSavedFilter(
                **{
                    fields_join(TemplateSavedFilter.title): SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED,
                    fields_join(TemplateSavedFilter.template): template,
                    fields_join(TemplateSavedFilter.filters): {
                        fields_join(ProfileAnnotationNames.HAS_EDUCATION): True,
                        fields_join(ProfileAnnotationNames.HAS_VERIFIED_EDUCATION): False,
                    },
                }
            ),
            SavedFilterNames.NO_WORK_EXPERIENCE: TemplateSavedFilter(
                **{
                    fields_join(TemplateSavedFilter.title): SavedFilterNames.NO_WORK_EXPERIENCE,
                    fields_join(TemplateSavedFilter.template): template,
                    fields_join(TemplateSavedFilter.filters): {
                        fields_join(ProfileAnnotationNames.HAS_WORK_EXPERIENCE): False,
                    },
                }
            ),
            SavedFilterNames.NO_CERTIFICATE: TemplateSavedFilter(
                **{
                    fields_join(TemplateSavedFilter.title): SavedFilterNames.NO_CERTIFICATE,
                    fields_join(TemplateSavedFilter.template): template,
                    fields_join(TemplateSavedFilter.filters): {
                        fields_join(ProfileAnnotationNames.HAS_CERTIFICATE): False,
                    },
                }
            ),
            SavedFilterNames.NO_LANGUAGE_CERTIFICATE: TemplateSavedFilter(
                **{
                    fields_join(TemplateSavedFilter.title): SavedFilterNames.NO_LANGUAGE_CERTIFICATE,
                    fields_join(TemplateSavedFilter.template): template,
                    fields_join(TemplateSavedFilter.filters): {
                        fields_join(ProfileAnnotationNames.HAS_LANGUAGE_CERTIFICATE): False,
                    },
                }
            ),
            SavedFilterNames.NO_VISA_STATUS: TemplateSavedFilter(
                **{
                    fields_join(TemplateSavedFilter.title): SavedFilterNames.NO_VISA_STATUS,
                    fields_join(TemplateSavedFilter.template): template,
                    fields_join(TemplateSavedFilter.filters): {
                        fields_join(ProfileAnnotationNames.HAS_CANADA_VISA): False,
                    },
                }
            ),
            SavedFilterNames.NO_JOB_INTEREST: TemplateSavedFilter(
                **{
                    fields_join(TemplateSavedFilter.title): SavedFilterNames.NO_JOB_INTEREST,
                    fields_join(TemplateSavedFilter.template): template,
                    fields_join(TemplateSavedFilter.filters): {
                        fields_join(ProfileAnnotationNames.HAS_INTERESTED_JOBS): False,
                    },
                }
            ),
        }

        TemplateSavedFilter.objects.bulk_create(
            filters_data.values(), ignore_conflicts=True, unique_fields=[fields_join(TemplateSavedFilter.filters)]
        )
        return filters_data

    def populate_campaigns(self):
        filters = self.populate_filters()

        campaigns_data = {
            SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION: Campaign(
                **{
                    fields_join(Campaign.title): SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION,
                    fields_join(Campaign.crontab): "0 0 */3 * *",
                    fields_join(Campaign.max_attempts): 3,
                    fields_join(Campaign.saved_filter): filters.get(SavedFilterNames.RESUME_UPLOADED_NO_INFORMATION),
                }
            ),
            SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED: Campaign(
                **{
                    fields_join(Campaign.title): SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED,
                    fields_join(Campaign.crontab): "0 0 */4 * *",
                    fields_join(Campaign.max_attempts): 3,
                    fields_join(Campaign.saved_filter): filters.get(SavedFilterNames.DEGREE_UPLOADED_NOT_VERIFIED),
                }
            ),
            SavedFilterNames.NO_WORK_EXPERIENCE: Campaign(
                **{
                    fields_join(Campaign.title): SavedFilterNames.NO_WORK_EXPERIENCE,
                    fields_join(Campaign.crontab): "0 0 */5 * *",
                    fields_join(Campaign.max_attempts): 3,
                    fields_join(Campaign.saved_filter): filters.get(SavedFilterNames.NO_WORK_EXPERIENCE),
                }
            ),
            SavedFilterNames.NO_CERTIFICATE: Campaign(
                **{
                    fields_join(Campaign.title): SavedFilterNames.NO_CERTIFICATE,
                    fields_join(Campaign.crontab): "0 0 */6 * *",
                    fields_join(Campaign.max_attempts): 3,
                    fields_join(Campaign.saved_filter): filters.get(SavedFilterNames.NO_CERTIFICATE),
                }
            ),
            SavedFilterNames.NO_LANGUAGE_CERTIFICATE: Campaign(
                **{
                    fields_join(Campaign.title): SavedFilterNames.NO_LANGUAGE_CERTIFICATE,
                    fields_join(Campaign.crontab): "0 0 */7 * *",
                    fields_join(Campaign.max_attempts): 3,
                    fields_join(Campaign.saved_filter): filters.get(SavedFilterNames.NO_LANGUAGE_CERTIFICATE),
                }
            ),
            SavedFilterNames.NO_VISA_STATUS: Campaign(
                **{
                    fields_join(Campaign.title): SavedFilterNames.NO_VISA_STATUS,
                    fields_join(Campaign.crontab): "0 0 */3 * *",
                    fields_join(Campaign.max_attempts): 3,
                    fields_join(Campaign.saved_filter): filters.get(SavedFilterNames.NO_VISA_STATUS),
                }
            ),
            SavedFilterNames.NO_JOB_INTEREST: Campaign(
                **{
                    fields_join(Campaign.title): SavedFilterNames.NO_JOB_INTEREST,
                    fields_join(Campaign.crontab): "0 0 */4 * *",
                    fields_join(Campaign.max_attempts): 3,
                    fields_join(Campaign.saved_filter): filters.get(SavedFilterNames.NO_JOB_INTEREST),
                }
            ),
        }
        Campaign.objects.bulk_create(
            campaigns_data.values(),
            update_conflicts=True,
            unique_fields=[fields_join(Campaign.saved_filter)],
            update_fields=[
                fields_join(Campaign.crontab),
                fields_join(Campaign.max_attempts),
                fields_join(Campaign.title),
            ],
        )

        notification_templates = [
            [
                NotificationTemplate(
                    **{
                        fields_join(NotificationTemplate.title): f"{campaign_title} Body",
                        fields_join(NotificationTemplate.content_template): render_to_string(
                            template_name=FILTER_TEMPLATE_MAPPER[campaign_templates]["body"]
                        ),
                    },
                ),
                NotificationTemplate(
                    **{
                        fields_join(NotificationTemplate.title): f"{campaign_title} Subject",
                        fields_join(NotificationTemplate.content_template): render_to_string(
                            template_name=FILTER_TEMPLATE_MAPPER[campaign_templates]["subject"]
                        ),
                    },
                ),
            ]
            for campaign_title, campaign_templates in FILTER_TEMPLATE_MAPPER.items()
        ]
        NotificationTemplate.objects.bulk_create(
            chain.from_iterable(notification_templates),
            ignore_conflicts=True,
            unique_fields=[fields_join(NotificationTemplate.title)],
        )

        campaign_notification_type_data = [
            CampaignNotificationType(
                **{
                    fields_join(CampaignNotificationType.campaign): campaign,
                    fields_join(CampaignNotificationType.notification_type): notification_type,
                    fields_join(CampaignNotificationType.body): NotificationTemplate.objects.filter(
                        {fields_join(NotificationTemplate.title): f"{campaign.title} Body"}
                    ).first(),
                    fields_join(CampaignNotificationType.subject): NotificationTemplate.objects.filter(
                        {fields_join(NotificationTemplate.title): f"{campaign.title} Subject"}
                    ).first(),
                }
            )
            for campaign in Campaign.objects.filter(
                **{fields_join(Campaign.title, In.lookup_name): list(campaigns_data.keys())}
            )
            for notification_type, _ in NotificationTypes.choices
        ]
        CampaignNotificationType.objects.bulk_create(campaign_notification_type_data, ignore_conflicts=True)

    def populate(self):
        self.populate_campaigns()
