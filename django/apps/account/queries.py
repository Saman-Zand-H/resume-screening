import graphene

from graphql_auth.queries import MeQuery

from .types import UserProfileType


# class ExtendedMeQuery(MeQuery):
#     profile = graphene.Field(UserProfileType)

#     def resolve_profile(self, info):
#         user = info.context.user
#         if user.is_authenticated:
#             return user.profile
#         raise None


class Query(MeQuery, graphene.ObjectType):
    pass
