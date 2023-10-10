from cities_light.graphql.types import City as CityTypeBase
from cities_light.graphql.types import Country as CountryTypeBase
from cities_light.graphql.types import Region as RegionTypeBase
from cities_light.graphql.types import SubRegion as SubRegionTypeBase
from cities_light.models import City, Country, Region, SubRegion
from graphene import relay
from query_optimizer import DjangoObjectType

from .models import Field, Job, University


class JobType(DjangoObjectType):
    class Meta:
        model = Job
        fields = (Job.id.field.name, Job.title.field.name)


class UniversityType(DjangoObjectType):
    class Meta:
        model = University
        fields = (
            University.id.field.name,
            University.name.field.name,
            University.city.field.name,
            University.website.field.name,
        )


class FieldType(DjangoObjectType):
    class Meta:
        model = Field
        fields = (Field.id.field.name, Field.name.field.name)


class CountryType(DjangoObjectType):
    class Meta:
        model = Country
        interfaces = (relay.Node,)
        fields = list(CountryTypeBase._meta.fields.keys())


class RegionType(DjangoObjectType):
    class Meta:
        model = Region
        fields = list(RegionTypeBase._meta.fields.keys())


class SubRegionType(DjangoObjectType):
    class Meta:
        model = SubRegion
        fields = list(SubRegionTypeBase._meta.fields.keys())


class CityNode(DjangoObjectType):
    class Meta:
        model = City
        interfaces = (relay.Node,)
        fields = list(CityTypeBase._meta.fields.keys())
        filter_fields = {
            City.display_name.field.name: ["icontains"],
        }
