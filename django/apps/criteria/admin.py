from account.models import User
from common.utils import fields_join

from django.contrib import admin
from django.contrib.admin import register
from django.utils.html import format_html

from .models import JobAssessment, JobAssessmentResult


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
    list_display = (
        JobAssessmentResult.user.field.name,
        JobAssessmentResult.job_assessment.field.name,
        JobAssessmentResult.score.field.name,
        JobAssessmentResult.raw_status.field.name,
        JobAssessmentResult.status.field.name,
        JobAssessmentResult.created_at.field.name,
        JobAssessmentResult.updated_at.field.name,
    )
    search_fields = (
        fields_join(
            JobAssessmentResult.user.field.name,
            User.email.field.name,
        ),
        fields_join(
            JobAssessmentResult.job_assessment.field.name,
            JobAssessment.title.field.name,
        ),
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
        "report_url_tag",
    )
    autocomplete_fields = (
        JobAssessmentResult.user.field.name,
        JobAssessmentResult.job_assessment.field.name,
    )

    def report_url_tag(self, obj):
        report_url = obj.report_url
        if not report_url:
            return "-"
        return format_html('<a href="{}">{}</a>', report_url, report_url)

    report_url_tag.short_description = "Report URL"
