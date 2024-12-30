from account.models import User
from common.utils import fj

from django.contrib import admin
from django.contrib.admin import register
from django.db.models import QuerySet
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import JobAssessment, JobAssessmentResult, JobAssessmentResultReportFile
from .tasks import download_report_file_task


class JobAssessmentInline(admin.TabularInline):
    model = JobAssessment.related_jobs.through
    extra = 1
    raw_id_fields = (JobAssessment.related_jobs.through.job.field.name,)


@admin.register(JobAssessment)
class JobAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        JobAssessment.title.field.name,
        JobAssessment.package_id.field.name,
        JobAssessment.short_description.field.name,
        JobAssessment.resumable.field.name,
    )
    search_fields = (JobAssessment.title.field.name, JobAssessment.package_id.field.name)
    list_filter = (JobAssessment.resumable.field.name,)
    inlines = (JobAssessmentInline,)


@register(JobAssessmentResult)
class JobAssessmentResultAdmin(admin.ModelAdmin):
    @admin.action(description=_("Download Report File"))
    def download_report_files(self, request, queryset: QuerySet[JobAssessmentResult]):
        for job_assessment_result in queryset:
            download_report_file_task.delay(job_assessment_result.pk)

        self.message_user(
            request,
            _("Report file download task for %(assessment_results)s has been scheduled.")
            % {"assessment_results": ", ".join(map(str, queryset))},
        )

    @admin.display(description=_("Report URL"))
    def report_url_tag(self, obj):
        report_url = obj.report_url
        if not report_url:
            return "-"
        return format_html('<a href="{}">{}</a>', report_url, report_url)

    @admin.display(description=_("Report File"))
    def report_file_tag(self, obj):
        report_file = JobAssessmentResultReportFile.objects.filter(
            **{fj(JobAssessmentResultReportFile.job_assessment_result): obj}
        ).first()
        if not report_file:
            return "-"

        return format_html('<a href="{}">{}</a>', report_file.file.url, report_file.file.name)

    list_display = (
        JobAssessmentResult.user.field.name,
        JobAssessmentResult.job_assessment.field.name,
        JobAssessmentResult.score.field.name,
        JobAssessmentResult.raw_status.field.name,
        JobAssessmentResult.status.field.name,
        JobAssessmentResult.created_at.field.name,
        JobAssessmentResult.updated_at.field.name,
    )
    actions = [download_report_files.__name__]
    search_fields = (
        fj(JobAssessmentResult.user, User.email),
        fj(JobAssessmentResult.job_assessment, JobAssessment.title),
        JobAssessmentResult.order_id.field.name,
    )
    list_filter = (
        JobAssessmentResult.status.field.name,
        JobAssessmentResult.created_at.field.name,
        JobAssessmentResult.updated_at.field.name,
    )
    readonly_fields = (
        JobAssessmentResult.score.field.name,
        JobAssessmentResult.status.field.name,
        JobAssessmentResult.order_id.field.name,
        report_url_tag.__name__,
        report_file_tag.__name__,
    )
    autocomplete_fields = (
        JobAssessmentResult.user.field.name,
        JobAssessmentResult.job_assessment.field.name,
    )
