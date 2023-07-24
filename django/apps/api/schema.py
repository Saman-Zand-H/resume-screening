import graphene
from account.schema import Query as AccountQuery


class Query(AccountQuery, graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
