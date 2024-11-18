from common.utils import fields_join
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType
from graphql_auth.queries import CountableConnection
from graphql_jwt.decorators import login_required

from .mixins import CourseUserContextMixin
from django.db.models.lookups import Exact

from .models import Course, CourseResult


class CourseNode(CourseUserContextMixin, DjangoObjectType):
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
            CourseResult.course.field.related_query_name(),
        )
        filter_fields = {
            Course.type.field.name: [Exact.lookup_name],
        }

    @classmethod
    @login_required
    def get_queryset(cls, queryset, info):
        return super().get_queryset(queryset, info).related_to_user(cls.get_user_context(info.context))


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
            fields_join(
                CourseResult.course,
                Course.type,
            ): [Exact.lookup_name],
            fields_join(CourseResult.status): [Exact.lookup_name],
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        user = cls.get_user_context(info.context)
        if not user:
            return queryset.none()
        return super().get_queryset(queryset, info).filter(**{fields_join(CourseResult.user): user})
