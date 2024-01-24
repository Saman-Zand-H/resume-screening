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
            JobAssessmentResult.status.field.name,
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

    def resolve_jobs(self, info):
        user = info.context.user
        return self.job_assessment_jobs.filter(job__in=user.profile.interested_jobs.values_list("pk", flat=True))

    @classmethod
    def fix_date(cls, date, time):
        return make_aware(datetime.datetime.combine(date, time))

    def resolve_results(self, info, filters=None):
        user = info.context.user
        if not user:
            return []

        results = JobAssessmentResult.objects.filter(job_assessment=self, user=user)
        filter_conditions = Q()
        fix_date = JobAssessmentType.fix_date
        if filters:
            filter_conditions = (
                Q(job_assessment=self, user=user)
                & Q(
                    created_at__range=(
                        fix_date(filters.created_at_start, datetime.time.min),
                        fix_date(filters.created_at_end, datetime.time.max),
                    )
                )
                & Q(
                    updated_at__range=(
                        fix_date(filters.updated_at_start, datetime.time.min),
                        fix_date(filters.updated_at_end, datetime.time.max),
                    )
                )
            )
        return results.filter(filter_conditions).order_by("-id")

    def resolve_can_retry(self, info):
        user = info.context.user
        return self.can_start(user)[0]

    def resolve_required(self, info):
        user = info.context.user
        return self.is_required(user.profile.interested_jobs.all())
