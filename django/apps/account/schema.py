import graphene
from graphene_django import DjangoObjectType

from django.contrib.auth import get_user_model

User = get_user_model()


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = "__all__"


class Query(graphene.ObjectType):
    users = graphene.List(UserType)


schema = graphene.Schema(query=Query)
