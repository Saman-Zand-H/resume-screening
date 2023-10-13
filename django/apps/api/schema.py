import graphene
from account.mutations import Mutation as AccountMutation
from account.queries import Query as AccountQuery
from common.queries import Query as CommonQuery
from common.mutations import Mutation as CommonMutation


class Query(AccountQuery, CommonQuery, graphene.ObjectType):
    pass


class Mutation(AccountMutation, CommonMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
