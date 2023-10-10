import graphene
from .types import UniversityType, FieldType
from .models import University, Field


class Query(graphene.ObjectType):
    universities = graphene.List(UniversityType)
    fields = graphene.List(FieldType)

    def resolve_universities(self, info):
        return University.objects.all()

    def resolve_fields(self, info):
        return Field.objects.all()
