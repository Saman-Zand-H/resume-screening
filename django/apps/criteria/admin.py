from django.contrib import admin
from django.contrib.admin import register

from .models import JobAssessment, JobAssessmentResult


class JobAssessmentInline(admin.TabularInline):
    model = JobAssessment.related_jobs.through
    extra = 1


@admin.register(JobAssessment)
class JobAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "package_id",
        "title",
        "description",
        "resumable",
    )
    search_fields = ("package_id",)
    list_filter = ("resumable",)
    inlines = (JobAssessmentInline,)


@register(JobAssessmentResult)
class JobAssessmentResultAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "job_assessment",
        "score",
        "status",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "user__email",
        "job_assessment__title",
        JobAssessmentResult.order_id.field.name,
    )
    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("score", JobAssessmentResult.order_id.field.name)
    raw_id_fields = (
        "user",
        "job_assessment",
    )
