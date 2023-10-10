import graphene
from common.types import JobType
from graphene_django.types import DjangoObjectType

from .models import UserProfile


class UserProfileType(DjangoObjectType):
    job = graphene.List(JobType)

    class Meta:
        model = UserProfile
        fields = (
            UserProfile.height.field.name,
            UserProfile.weight.field.name,
            UserProfile.skin_color.field.name,
            UserProfile.hair_color.field.name,
            UserProfile.eye_color.field.name,
            UserProfile.full_body_image.field.name,
            UserProfile.job.field.name,
        )

    def resolve_job(self, info):
        return self.job.all()
