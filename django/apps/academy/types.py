from account.models import Profile
from common.models import Industry
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from django.db.models import Q

from .models import Course, CourseResult


class CourseNode(DjangoObjectType):
    class Meta:
        model = Course
        use_connection = True
        fields = (
            Course.id.field.name,
            Course.name.field.name,
            Course.description.field.name,
            Course.logo.field.name,
            Course.external_id.field.name,
            Course.type.field.name,
            Course.industries.field.name,
            Course.url.field.name,
            CourseResult.course.field.related_query_name(),
        )
        filter_fields = {
            Course.type.field.name: ["exact"],
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        user = info.context.user
        if not user or not (profile := user.get_profile()):
            return queryset.none()

        jobs = profile.interested_jobs.all()
        industries = Industry.objects.filter(jobcategory__job__in=jobs).distinct().values_list("id", flat=True)
        return (
            super().get_queryset(queryset, info).filter(Q(industries__in=industries) | Q(is_required=True)).distinct()
        )


class CourseResultType(DjangoObjectType):
    class Meta:
        model = CourseResult
        use_connection = True
        fields = (
            CourseResult.id.field.name,
            CourseResult.user.field.name,
            CourseResult.course.field.name,
            CourseResult.status.field.name,
            CourseResult.created_at.field.name,
            CourseResult.updated_at.field.name,
        )

        filter_fields = {
            f"{CourseResult.course.field.name}__{Course.type.field.name}": ["exact"],
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        user = info.context.user
        if not user:
            return queryset.none()
        return super().get_queryset(queryset, info).filter(user=user)
