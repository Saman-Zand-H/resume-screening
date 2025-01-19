from common.logging import get_logger
from common.utils import fj
from config.settings.subscriptions import AssessmentSubscription
from flex_pubsub.tasks import register_task
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from django.db.models.lookups import IsNull

from .constants import CRITERIA_REPORT_FILE_DOWNLOAD_RETRY_ATTEMPTS
from .models import JobAssessmentResult, JobAssessmentResultReportFile
from .utils import download_report_file

logger = get_logger()


@register_task([AssessmentSubscription.REPORT_FILE])
def download_report_file_task(job_assessment_result_id: int):
    if not (
        assessment_result := JobAssessmentResult.objects.select_related(fj(JobAssessmentResult.user))
        .filter(
            **{
                JobAssessmentResult._meta.pk.attname: job_assessment_result_id,
                fj(JobAssessmentResult.report_url, IsNull.lookup_name): False,
                fj(
                    JobAssessmentResultReportFile.job_assessment_result.field.related_query_name(),
                    IsNull.lookup_name,
                ): True,
            }
        )
        .first()
    ):
        logger.warning(
            f"Request failed to download report pdf for result with id {job_assessment_result_id}. No result found."
        )
        return

    file_name = f"{assessment_result.order_id}.pdf"

    try:

        @retry(
            stop=stop_after_attempt(CRITERIA_REPORT_FILE_DOWNLOAD_RETRY_ATTEMPTS),
            wait=wait_exponential(multiplier=1, min=4, max=60),
        )
        def download_with_retry(url, name):
            return download_report_file(url, name)

        file = download_with_retry(assessment_result.report_url, file_name)

        JobAssessmentResultReportFile.objects.create(
            **{
                fj(JobAssessmentResultReportFile.job_assessment_result): assessment_result,
                fj(JobAssessmentResultReportFile.file): file,
            }
        )

    except RetryError as retry_error:
        original_exception = retry_error.last_attempt.exception()
        if original_exception:
            logger.error(
                f"Failed to download report pdf for result with id {job_assessment_result_id}. "
                f"Original error: {original_exception}"
            )
        else:
            logger.error(f"Failed to download report pdf for result with id {job_assessment_result_id}. {retry_error}")
        return
    except Exception as e:
        logger.error(f"Failed to download report pdf for result with id {job_assessment_result_id}. {e}")
        return
