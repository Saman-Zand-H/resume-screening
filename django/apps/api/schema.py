import graphene
from account.mutations import Mutation as AccountMutation
from account.queries import Query as AccountQuery
from common.mutations import Mutation as CommonMutation
from common.queries import Query as CommonQuery
from criteria.mutations import Mutation as CriteriaMutation


class Query(AccountQuery, CommonQuery, graphene.ObjectType):
    pass


class Mutation(AccountMutation, CriteriaMutation, CommonMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
