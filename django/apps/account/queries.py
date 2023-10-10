import graphene
from graphql_auth.queries import MeQuery


class Query(MeQuery, graphene.ObjectType):
    pass
