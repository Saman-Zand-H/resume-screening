import graphene
from common.utils import fj
from common.decorators import login_required
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType
from graphql_auth.queries import CountableConnection

from django.db.models.lookups import Exact

from .mixins import CourseUserContextMixin
from .models import Course, CourseResult


class CourseNode(CourseUserContextMixin, DjangoObjectType):
    is_general = graphene.Boolean(source=Course.is_general.fget.__name__)

    class Meta:
        model = Course
        use_connection = True
        fields = (
            Course.id.field.name,
            Course.name.field.name,
            Course.description.field.name,
            Course.logo.field.name,
            Course.external_id.field.name,
            Course.industries.field.name,
            CourseResult.course.field.related_query_name(),
        )
        filter_fields = {}

    @classmethod
    @login_required
    def get_queryset(cls, queryset, info):
        return super().get_queryset(queryset, info).related_to_user(cls.get_obj_context(info.context))


class CourseResultType(CourseUserContextMixin, DjangoObjectType):
    class Meta:
        model = CourseResult
        use_connection = True
        connection_class = CountableConnection
        fields = (
            CourseResult.id.field.name,
            CourseResult.user.field.name,
            CourseResult.course.field.name,
            CourseResult.status.field.name,
            CourseResult.created_at.field.name,
            CourseResult.updated_at.field.name,
        )

        filter_fields = {
            fj(CourseResult.status): [Exact.lookup_name],
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        user = cls.get_obj_context(info.context)
        if not user:
            return queryset.none()
        return super().get_queryset(queryset, info).filter(**{fj(CourseResult.user): user})
