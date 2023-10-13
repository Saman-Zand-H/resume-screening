import graphene
from common.types import JobType
from query_optimizer import DjangoObjectType

from .models import Profile, Education


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



class EducationType(DjangoObjectType):
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
        )
