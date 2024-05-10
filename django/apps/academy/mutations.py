import graphene
from account.mixins import DocumentCUDMixin
from graphene_django_cud.mutations import DjangoCreateMutation

from .models import CourseResult


class CourseResultCreateMutation(DocumentCUDMixin, DjangoCreateMutation):
    start_url = graphene.String(required=True)

    class Meta:
        model = CourseResult
        fields = (CourseResult.course.field.name,)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        cls.full_clean(obj)

    @classmethod
    def after_mutate(cls, root, info, input, obj, return_data):
        return_data["start_url"] = obj.course.url or "https://example.com"
        return super().after_mutate(root, info, input, obj, return_data)


class AcademyMutation(graphene.ObjectType):
    start_course = CourseResultCreateMutation.Field()


class Mutation(graphene.ObjectType):
    academy = graphene.Field(AcademyMutation, required=True)

    def resolve_academy(self, *args, **kwargs):
        return AcademyMutation()
