import graphene
from account.mixins import DocumentCUDMixin
from graphene_django_cud.mutations import DjangoCreateMutation

from criteria.client.client import criteria_client
from criteria.client.types import CreateOrderRequest, Identifier
from django.core.exceptions import ValidationError

from .models import JobAssessment, JobAssessmentResult


class JobAssessmentCreateMutation(DocumentCUDMixin, DjangoCreateMutation):
    assessment_access_url = graphene.String(required=True)

    class Meta:
        model = JobAssessmentResult
        fields = (JobAssessmentResult.job_assessment.field.name,)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        cls.full_clean(obj)

    @classmethod
    def validate(cls, root, info, input):
        user = info.context.user
        job_assessment_id = input.get(JobAssessmentResult.job_assessment.field.name)

        if not JobAssessment.objects.related_to_user(user).filter(pk=job_assessment_id).exists():
            raise ValidationError("Not related to the user.")

        job_assessment = JobAssessment.objects.get(id=job_assessment_id)
        _, error_message = job_assessment.can_start(user)
        if error_message:
            raise ValidationError(error_message)

        return super().validate(root, info, input)

    @classmethod
    def after_mutate(cls, root, info, input, obj, return_data):
        assessment_access_url = criteria_client.create_order(
            CreateOrderRequest(
                packageId=Identifier(value=obj.job_assessment.package_id),
                orderId=Identifier(value=str(obj.order_id)),
                externalId=Identifier(value=str(obj.pk)),
            )
        ).assessmentAccessURL
        return_data["assessment_access_url"] = assessment_access_url.uri
        return super().after_mutate(root, info, input, obj, return_data)


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
