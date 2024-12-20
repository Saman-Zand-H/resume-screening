import graphene
from account.mixins import CRUDWithoutIDMutationMixin, DocumentCUDMixin
from graphene_django_cud.mutations import DjangoUpdateMutation

from django.db import transaction

from .models import CourseResult

from common.decorators import login_required


@login_required()
class CourseResultCreateMutation(DocumentCUDMixin, CRUDWithoutIDMutationMixin, DjangoUpdateMutation):
    start_url = graphene.String(required=True)

    class Meta:
        model = CourseResult
        fields = (CourseResult.course.field.name,)

    @classmethod
    def get_object_id(cls, context):
        info = context.get("info")
        course_id = context.get("input").get(CourseResult.course.field.name)
        course_result = CourseResult.objects.get_or_create(user=info.context.user, course_id=course_id)[0]
        return course_result.id

    @classmethod
    @transaction.atomic
    def mutate(cls, *args, **kwargs):
        return super().mutate(*args, **kwargs)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        cls.full_clean(obj)

    @classmethod
    def after_mutate(cls, root, info, id, input, obj: CourseResult, return_data):
        return_data["start_url"] = obj.get_login_url()
        return super().after_mutate(root, info, id, input, obj, return_data)


class AcademyMutation(graphene.ObjectType):
    start_course = CourseResultCreateMutation.Field()


class Mutation(graphene.ObjectType):
    academy = graphene.Field(AcademyMutation, required=True)

    def resolve_academy(self, *args, **kwargs):
        return AcademyMutation()
