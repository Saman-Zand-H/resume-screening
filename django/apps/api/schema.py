import graphene
from account.mutations import Mutation as AccountMutation
from account.queries import Query as AccountQuery
from common.mutations import Mutation as CommonMutation
from common.queries import Query as CommonQuery
from criteria.mutations import Mutation as CriteriaMutation
from academy.queries import Query as AcademyQuery
from academy.mutations import Mutation as AcademyMutation


class Query(AccountQuery, CommonQuery, AcademyQuery, graphene.ObjectType):
    pass


class Mutation(AccountMutation, CriteriaMutation,AcademyMutation, CommonMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
