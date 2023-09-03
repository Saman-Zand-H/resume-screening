import graphene
from account.mutations import Mutation as AccountMutation
from account.queries import Query as AccountQuery

from .mutations import Mutation as TestMutation
from .queries import Query as TestQuery


class Query(AccountQuery, TestQuery, graphene.ObjectType):
    pass


class Mutation(AccountMutation, TestMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
