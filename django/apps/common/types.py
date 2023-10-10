from graphene_django.types import DjangoObjectType
from .models import Job


class JobType(DjangoObjectType):
    class Meta:
        model = Job
        fields = (Job.id.field.name, Job.title.field.name)
