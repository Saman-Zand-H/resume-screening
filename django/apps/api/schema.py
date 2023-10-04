import graphene
from account.mutations import Mutation as AccountMutation
from account.queries import Query as AccountQuery


class Query(AccountQuery, graphene.ObjectType):
    pass


class Mutation(AccountMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
