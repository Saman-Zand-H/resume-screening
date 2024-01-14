import graphene
from graphene_django_cud.mutations import DjangoCreateMutation

from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

from .models import JobAssessmentResult, JobAssessmentJob

from account.mixins import DocumentCUDMixin


class JobAssessmentCreateMutation(DocumentCUDMixin, DjangoCreateMutation):
    class Meta:
        model = JobAssessmentResult
        fields = (
            JobAssessmentResult.job_assessment.field.name,
            JobAssessmentResult.raw_score.field.name,
        )

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        cls.full_clean(obj)

    @classmethod
    def validate(cls, root, info, input):
        user = info.context.user
        job_assessment_id = input.get(JobAssessmentResult.job_assessment.field.name)

        if not user.profile.interested_jobs.filter(assessments=job_assessment_id).exists():
            raise ValidationError({JobAssessmentResult.job_assessment.field.name: "Not related to the user."})

        last_result = (
            JobAssessmentResult.objects.filter(job_assessment_id=job_assessment_id, user=user)
            .only("status", "updated_at")
            .last()
        )

        if last_result:
            if last_result.status in [JobAssessmentResult.Status.COMPLETED, JobAssessmentResult.Status.TIMEOUT]:
                retry_interval = (
                    JobAssessmentJob.objects.filter(job_assessment_id=job_assessment_id)
                    .values_list("retry_interval", flat=True)
                    .first()
                ) or timedelta(weeks=1)
                if last_result.updated_at + retry_interval >= timezone.now():
                    raise ValidationError(
                        {JobAssessmentResult.job_assessment.field.name: "You can't start a new assessment yet."}
                    )
            else:
                raise ValidationError(
                    {JobAssessmentResult.job_assessment.field.name: "There is an incomplete assessment."}
                )

        return super().validate(root, info, input)


class JobAssessmentMutation(graphene.ObjectType):
    start = JobAssessmentCreateMutation.Field()


class CriteriaMutation(graphene.ObjectType):
    job_assessment = graphene.Field(JobAssessmentMutation)

    def resolve_job_assessment(self, *args, **kwargs):
        return JobAssessmentMutation()


class Mutation(graphene.ObjectType):
    criteria = graphene.Field(CriteriaMutation, required=True)

    def resolve_criteria(self, *args, **kwargs):
        return CriteriaMutation()
