import graphene
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from django.utils import timezone
from datetime import timedelta

from .models import JobAssessment, JobAssessmentResult, JobAssessmentJob

from account.mixins import FilterQuerySetByUserMixin


class JobAssessmentResultFilterInput(graphene.InputObjectType):
    created_at_start = graphene.Date()
    created_at_end = graphene.Date()
    updated_at_start = graphene.Date()
    updated_at_end = graphene.Date()


class JobAssessmentFilterInput(graphene.InputObjectType):
    required = graphene.Boolean()
    no_results = graphene.Boolean()


class JobAssessmentResultNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = JobAssessmentResult
        interfaces = (graphene.relay.Node,)
        fields = (
            JobAssessmentResult.id.field.name,
            JobAssessmentResult.status.field.name,
            JobAssessmentResult.score.field.name,
            JobAssessmentResult.created_at.field.name,
            JobAssessmentResult.updated_at.field.name,
        )


class JobAssessmentJobNode(DjangoObjectType):
    class Meta:
        model = JobAssessmentJob
        interfaces = (graphene.relay.Node,)
        fields = (
            JobAssessmentJob.id.field.name,
            JobAssessmentJob.job.field.name,
            JobAssessmentJob.required.field.name,
        )


class JobAssessmentNode(DjangoObjectType):
    jobs = graphene.List(JobAssessmentJobNode)
    results = graphene.List(
        JobAssessmentResultNode, filters=graphene.Argument(JobAssessmentResultFilterInput, required=False)
    )
    can_retry = graphene.Boolean()

    class Meta:
        model = JobAssessment
        interfaces = (graphene.relay.Node,)
        fields = (
            JobAssessment.id.field.name,
            JobAssessment.service_id.field.name,
            JobAssessment.title.field.name,
            JobAssessment.logo.field.name,
            JobAssessment.short_description.field.name,
            JobAssessment.description.field.name,
            JobAssessment.resumable.field.name,
        )

    def resolve_jobs(self, info):
        user = info.context.user
        return self.job_assessment_jobs.filter(job__in=user.profile.interested_jobs.values_list("pk", flat=True))

    def resolve_results(self, info, filters=None):
        user = info.context.user
        if not user:
            return []

        results = JobAssessmentResult.objects.filter(job_assessment=self, user=user).order_by("-id")

        if filters:
            if filters.created_at_start and filters.created_at_end:
                results = results.filter(created_at__range=[filters.created_at_start, filters.created_at_end])

            if filters.updated_at_start and filters.updated_at_end:
                results = results.filter(updated_at__range=[filters.updated_at_start, filters.updated_at_end])
        return results

    def resolve_can_retry(self, info):
        user = info.context.user
        last_result = JobAssessmentResult.objects.filter(job_assessment=self, user=user).last()
        if not last_result:
            return True
        if last_result.status in [JobAssessmentResult.Status.COMPLETED, JobAssessmentResult.Status.TIMEOUT]:
            retry_interval = (
                JobAssessmentJob.objects.filter(job_assessment=self).values_list("retry_interval", flat=True).first()
            ) or timedelta(weeks=1)
            return last_result.updated_at + retry_interval < timezone.now()
        return False
