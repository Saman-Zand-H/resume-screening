import graphene
from common.types import JobType
from query_optimizer import DjangoObjectType

from .models import CommunicationMethod, Education, IEEMethod, Profile


class ProfileType(DjangoObjectType):
    job = graphene.List(JobType)

    class Meta:
        model = Profile
        fields = (
            Profile.height.field.name,
            Profile.weight.field.name,
            Profile.skin_color.field.name,
            Profile.hair_color.field.name,
            Profile.eye_color.field.name,
            Profile.full_body_image.field.name,
            Profile.job.field.name,
        )

    def resolve_job(self, info):
        return self.job.all()


class EducationMethodFieldTypes(graphene.ObjectType):
    method = graphene.String()
    field = graphene.String()


class EducationType(DjangoObjectType):
    method_fields = graphene.List(EducationMethodFieldTypes)

    class Meta:
        model = Education
        fields = (
            Education.id.field.name,
            Education.field.field.name,
            Education.degree.field.name,
            Education.university.field.name,
            Education.start.field.name,
            Education.end.field.name,
            Education.status.field.name,
            Education.created_at.field.name,
            Education.updated_at.field.name,
            IEEMethod.get_related_name(),
            CommunicationMethod.get_related_name(),
        )

    def resolve_method_fields(self, info):
        return [
            EducationMethodFieldTypes(method=method, field=model.get_related_name() if model else None)
            for method, model in self.get_method_choices().items()
        ]


class IEEMethodType(DjangoObjectType):
    class Meta:
        model = IEEMethod
        fields = (
            IEEMethod.id.field.name,
            IEEMethod.ices_document.field.name,
            IEEMethod.citizen_document.field.name,
            IEEMethod.evaluator.field.name,
        )


class CommunicationMethodType(DjangoObjectType):
    class Meta:
        model = CommunicationMethod
        fields = (
            CommunicationMethod.id.field.name,
            CommunicationMethod.email.field.name,
            CommunicationMethod.department.field.name,
            CommunicationMethod.person.field.name,
            CommunicationMethod.degree_file.field.name,
        )
