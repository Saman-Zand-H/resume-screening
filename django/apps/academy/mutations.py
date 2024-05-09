import graphene

from .models import Course
from common.models import Industry


class StartCourseMutation(graphene.Mutation):
    class Arguments:
        course_id = graphene.ID()

    url = graphene.String()

    @classmethod
    def mutate(cls, root, info, course_id):
        user = info.context.user
        if user:
            jobs = user.profile.interested_jobs.all()
            if Industry.objects.filter(jobcategory__job__in=jobs, course=course_id).exists():
                return StartCourseMutation(url="https://www.google.com")
        return StartCourseMutation(url=None)


class AcademyMutation(graphene.ObjectType):
    start_course = StartCourseMutation.Field()


class Mutation(graphene.ObjectType):
    academy = graphene.Field(AcademyMutation, required=True)

    def resolve_academy(self, *args, **kwargs):
        return AcademyMutation()
