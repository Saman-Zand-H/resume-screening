from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from .models import Course
from common.models import Industry


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
        )
        filter_fields = {
            Course.id.field.name: ["exact"],
            Course.name.field.name: ["icontains"],
            Course.external_id.field.name: ["exact"],
            Course.type.field.name: ["exact"],
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        user = info.context.user
        if not user:
            return queryset.none()

        jobs = user.profile.interested_jobs.all()
        industries = Industry.objects.filter(jobcategory__job__in=jobs).distinct().values_list("id", flat=True)
        return super().get_queryset(queryset, info).filter(industries__in=industries).distinct()
