import datetime

import graphene
from account.mixins import FilterQuerySetByUserMixin
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from django.db.models import Q
from django.utils.timezone import make_aware

from .models import JobAssessment, JobAssessmentJob, JobAssessmentResult


class JobAssessmentResultFilterInput(graphene.InputObjectType):
    created_at_start = graphene.Date(default_value=datetime.date.min)
    created_at_end = graphene.Date(default_value=datetime.date.max)
    updated_at_start = graphene.Date(default_value=datetime.date.min)
    updated_at_end = graphene.Date(default_value=datetime.date.max)


class JobAssessmentFilterInput(graphene.InputObjectType):
    required = graphene.Boolean()


class JobAssessmentResultType(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = JobAssessmentResult
        fields = (
            JobAssessmentResult.id.field.name,
            JobAssessmentResult.score.field.name,
            JobAssessmentResult.created_at.field.name,
            JobAssessmentResult.updated_at.field.name,
        )


class JobAssessmentJobType(DjangoObjectType):
    class Meta:
        model = JobAssessmentJob
        fields = (
            JobAssessmentJob.id.field.name,
            JobAssessmentJob.job.field.name,
            JobAssessmentJob.required.field.name,
        )


class JobAssessmentType(DjangoObjectType):
    jobs = graphene.List(JobAssessmentJobType)
    results = graphene.List(
        JobAssessmentResultType, filters=graphene.Argument(JobAssessmentResultFilterInput, required=False)
    )
    can_retry = graphene.Boolean()
    required = graphene.Boolean()

    class Meta:
        model = JobAssessment
        fields = (
            JobAssessment.id.field.name,
            JobAssessment.title.field.name,
            JobAssessment.logo.field.name,
            JobAssessment.short_description.field.name,
            JobAssessment.description.field.name,
            JobAssessment.resumable.field.name,
        )

    @classmethod
    def get_user(cls, info):
        return getattr(info.context, "job_assessment_user", info.context.user)

    def resolve_jobs(self, info):
        interested_jobs = JobAssessmentType.get_user(info).profile.interested_jobs.values_list("pk", flat=True)
        return self.job_assessment_jobs.filter(job__in=interested_jobs)

    def resolve_results(self, info, filters=None):
        user = JobAssessmentType.get_user(info)
        if not user:
            return []

        results = JobAssessmentResult.objects.filter(
            job_assessment=self,
            user=user,
            status=JobAssessmentResult.Status.COMPLETED,
        )

        filter_conditions = Q()
        if filters:
            filter_conditions = Q(created_at__date__range=(filters.created_at_start, filters.created_at_end)) & Q(
                updated_at__date__range=(filters.updated_at_start, filters.updated_at_end)
            )

        return results.filter(filter_conditions).order_by(f"-{JobAssessmentResult.updated_at.field.name}")

    def resolve_can_retry(self, info):
        return self.can_start(JobAssessmentType.get_user(info))[0]

    def resolve_required(self, info):
        return self.is_required(JobAssessmentType.get_user(info).profile.interested_jobs.all())
