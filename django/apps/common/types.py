from cities_light.graphql.types import City as CityTypeBase
from cities_light.graphql.types import Country as CountryTypeBase
from cities_light.graphql.types import Region as RegionTypeBase
from cities_light.graphql.types import SubRegion as SubRegionTypeBase
from cities_light.models import City, Country, Region, SubRegion
from graphene import relay
from query_optimizer import DjangoObjectType

from .models import Field, Job, University


class JobNode(DjangoObjectType):
    class Meta:
        model = Job
        interfaces = (relay.Node,)
        fields = (
            Job.id.field.name,
            Job.title.field.name,
        )


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
