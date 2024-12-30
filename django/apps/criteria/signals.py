from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import JobAssessmentResult
from .tasks import download_report_file_task


@receiver(post_save, sender=JobAssessmentResult)
def download_report_file_on_save(sender, instance: JobAssessmentResult, created, **kwargs):
    if instance.status == JobAssessmentResult.Status.COMPLETED and instance.report_url:
        download_report_file_task.delay(instance.pk)
