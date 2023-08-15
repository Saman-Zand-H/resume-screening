import graphene
from account.schema import Query as AccountQuery
from account.schema import Mutation as AccountMutation


class Query(AccountQuery, graphene.ObjectType):
    pass


class Mutation(AccountMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
