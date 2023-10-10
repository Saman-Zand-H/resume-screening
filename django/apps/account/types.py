import graphene
from common.types import JobType
from query_optimizer import DjangoObjectType

from .models import Profile


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
