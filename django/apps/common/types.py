from graphene_django.types import DjangoObjectType
from .models import Job, University, Field


class JobType(DjangoObjectType):
    class Meta:
        model = Job
        fields = (Job.id.field.name, Job.title.field.name)


class UniversityType(DjangoObjectType):
    class Meta:
        model = University
        fields = (
            University.id.field.name,
            University.name.field.name,
            University.city.field.name,
            University.website.field.name,
        )


class FieldType(DjangoObjectType):
    class Meta:
        model = Field
        fields = (Field.id.field.name, Field.name.field.name)
