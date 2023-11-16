import graphene
from graphql_auth.queries import MeQuery
from graphql_jwt.decorators import login_required

from .types import EducationType


class EducationQuery(graphene.ObjectType):
    get = graphene.Field(EducationType, id=graphene.Int())

    @login_required
    def resolve_get(self, info, id):
        return EducationType.get_node(info, id)


class Query(MeQuery, graphene.ObjectType):
    education = graphene.Field(EducationQuery)

    def resolve_education(self, info):
        return EducationQuery()
