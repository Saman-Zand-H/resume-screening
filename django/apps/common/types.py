from cities_light.graphql.types import City as CityTypeBase
from cities_light.graphql.types import Country as CountryTypeBase
from cities_light.graphql.types import Region as RegionTypeBase
from cities_light.graphql.types import SubRegion as SubRegionTypeBase
from cities_light.models import City, Country, Region, SubRegion
import graphene
from graphene import Enum, relay
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from .exceptions import Error, Errors
from .models import (
    Field,
    Job,
    JobAssessment,
    JobAssessmentJob,
    JobCategory,
    JobIndustry,
    Language,
    LanguageProficiencyTest,
    Position,
    Skill,
    University,
)

enum_values = [(v.code, v.message) for k, v in vars(Errors).items() if isinstance(v, Error)]
ErrorType = Enum("Errors", enum_values)


class JobIndustryNode(DjangoObjectType):
    class Meta:
        model = JobIndustry
        interfaces = (relay.Node,)
        fields = (
            JobIndustry.id.field.name,
            JobIndustry.title.field.name,
        )
        filter_fields = {
            JobIndustry.title.field.name: ["icontains"],
        }


class JobCategoryNode(DjangoObjectType):
    class Meta:
        model = JobCategory
        interfaces = (relay.Node,)
        fields = (
            JobCategory.id.field.name,
            JobCategory.title.field.name,
        )
        filter_fields = {
            JobCategory.title.field.name: ["icontains"],
        }


class JobNode(DjangoObjectType):
    class Meta:
        model = Job
        interfaces = (relay.Node,)
        fields = (
            Job.id.field.name,
            Job.title.field.name,
            Job.category.field.name,
            Job.industry.field.name,
        )
        filter_fields = {
            Job.title.field.name: ["icontains"],
            Job.category.field.name: ["exact"],
            Job.industry.field.name: ["exact"],
        }


class UniversityNode(DjangoObjectType):
    class Meta:
        model = University
        interfaces = (relay.Node,)
        fields = (
            University.id.field.name,
            University.name.field.name,
            University.city.field.name,
            University.website.field.name,
        )
        filter_fields = {
            University.name.field.name: ["icontains"],
        }


class FieldNode(DjangoObjectType):
    class Meta:
        model = Field
        interfaces = (relay.Node,)
        fields = (
            Field.id.field.name,
            Field.name.field.name,
        )
        filter_fields = {
            Field.name.field.name: ["icontains"],
        }


class CountryNode(DjangoObjectType):
    class Meta:
        model = Country
        interfaces = (relay.Node,)
        fields = list(CountryTypeBase._meta.fields.keys())
        filter_fields = {
            Country.name.field.name: ["icontains"],
        }


class RegionNode(DjangoObjectType):
    class Meta:
        model = Region
        interfaces = (relay.Node,)
        fields = list(RegionTypeBase._meta.fields.keys())
        filter_fields = {
            Region.name.field.name: ["icontains"],
            Region.country.field.name: ["exact"],
        }


class SubRegionNode(DjangoObjectType):
    class Meta:
        model = SubRegion
        interfaces = (relay.Node,)
        fields = list(SubRegionTypeBase._meta.fields.keys())


class CityNode(DjangoObjectType):
    class Meta:
        model = City
        interfaces = (relay.Node,)
        fields = list(CityTypeBase._meta.fields.keys())
        filter_fields = {
            City.name.field.name: ["icontains"],
            City.region.field.name: ["exact"],
        }


class LanguageNode(DjangoObjectType):
    class Meta:
        model = Language
        interfaces = (relay.Node,)
        fields = (
            Language.id.field.name,
            Language.name.field.name,
            Language.code.field.name,
        )
        filter_fields = {
            Language.name.field.name: ["icontains"],
        }


class LanguageProficiencyTestNode(DjangoObjectType):
    class Meta:
        model = LanguageProficiencyTest
        interfaces = (relay.Node,)
        fields = (
            LanguageProficiencyTest.id.field.name,
            LanguageProficiencyTest.title.field.name,
            LanguageProficiencyTest.min_score.field.name,
            LanguageProficiencyTest.max_score.field.name,
        )
        filter_fields = {
            LanguageProficiencyTest.title.field.name: ["icontains"],
        }


class PositionNode(DjangoObjectType):
    class Meta:
        model = Position
        interfaces = (relay.Node,)
        fields = (
            Position.id.field.name,
            Position.title.field.name,
        )
        filter_fields = {
            Position.title.field.name: ["icontains"],
        }


class SkillNode(DjangoObjectType):
    class Meta:
        model = Skill
        interfaces = (relay.Node,)
        fields = (
            Skill.id.field.name,
            Skill.title.field.name,
        )
        filter_fields = {
            Skill.title.field.name: ["icontains"],
        }


class JobAssessmentJobNode(DjangoObjectType):
    class Meta:
        model = JobAssessmentJob
        interfaces = (relay.Node,)
        fields = (
            JobAssessmentJob.id.field.name,
            JobAssessmentJob.job.field.name,
            JobAssessmentJob.required.field.name,
        )


class JobAssessmentNode(DjangoObjectType):
    jobs = graphene.List(JobAssessmentJobNode)

    class Meta:
        model = JobAssessment
        interfaces = (relay.Node,)
        fields = (
            JobAssessment.id.field.name,
            JobAssessment.service_id.field.name,
            JobAssessment.title.field.name,
            JobAssessment.logo.field.name,
            JobAssessment.short_description.field.name,
            JobAssessment.description.field.name,
            JobAssessment.resumable.field.name,
        )

        filter_fields = {
            JobAssessment.related_jobs.field.name: ["exact"],
            JobAssessment.title.field.name: ["icontains"],
            JobAssessment.service_id.field.name: ["icontains"],
            JobAssessment.resumable.field.name: ["exact"],
            "job_assessment_jobs__required": ["exact"],
        }

    def resolve_jobs(self, info):
        user = info.context.user
        return self.job_assessment_jobs.filter(job__in=user.profile.interested_jobs.values_list("pk", flat=True))
