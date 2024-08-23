import graphene
from account.mutations import Mutation as AccountMutation
from account.queries import Query as AccountQuery
from common.mutations import Mutation as CommonMutation
from common.queries import Query as CommonQuery
from criteria.mutations import Mutation as CriteriaMutation
from academy.queries import Query as AcademyQuery
from academy.mutations import Mutation as AcademyMutation
from cv.mutations import Mutation as CVMutation
from cv.queries import Query as CVQuery
from notification.mutations import Mutation as NotificationMutation


class Query(AccountQuery, CommonQuery, AcademyQuery, CVQuery, graphene.ObjectType):
    pass


class Mutation(
    AccountMutation,
    CriteriaMutation,
    AcademyMutation,
    CVMutation,
    NotificationMutation,
    CommonMutation,
    graphene.ObjectType,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
