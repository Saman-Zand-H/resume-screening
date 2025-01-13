from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import JobAssessmentResult, JobAssessmentResultReportFile
from .tasks import download_report_file_task


@receiver(post_save, sender=JobAssessmentResult)
def download_report_file_on_save(sender, instance: JobAssessmentResult, created, **kwargs):
    if instance.report_url and not hasattr(
        instance, JobAssessmentResultReportFile.job_assessment_result.field.related_query_name()
    ):
        download_report_file_task.delay(instance.pk)
