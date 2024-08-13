from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from .models import CVTemplate, GeneratedCV, GeneratedCVContent


class CVTemplateNode(DjangoObjectType):
    class Meta:
        model = CVTemplate
        use_connection = True
        fields = (
            CVTemplate.id.field.name,
            CVTemplate.title.field.name,
        )
        filter_fields = {
            CVTemplate.title.field.name: ["icontains"],
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        return super().get_queryset(queryset, info).filter(is_active=True)


class GeneratedCVNode(DjangoObjectType):
    class Meta:
        model = GeneratedCV
        use_connection = True
        fields = (GeneratedCV.file.field.name,)


class GeneratedCVContentType(DjangoObjectType):
    class Meta:
        model = GeneratedCVContent
        fields = (GeneratedCVContent.about_me.field.name,)


class JobSeekerGeneratedCVType(DjangoObjectType):
    class Meta:
        model = GeneratedCV
        fields = (
            GeneratedCV.file.field.name,
            GeneratedCV.modified.field.name,
        )
