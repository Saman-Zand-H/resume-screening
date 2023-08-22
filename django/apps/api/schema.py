import graphene
from account.schema import Mutation as AccountMutation
from account.schema import Query as AccountQuery


class AddNumber(graphene.Mutation):
    class Arguments:
        number = graphene.Int()

    sum = graphene.Int()

    def mutate(self, info, number):
        return AddNumber(sum=number + 1)


class TestQuery(graphene.ObjectType):
    ping = graphene.String()

    def resolve_ping(self, info):
        return "pong"


class TestMutation(graphene.ObjectType):
    add_number = AddNumber.Field()


class Query(AccountQuery, TestQuery, graphene.ObjectType):
    pass


class Mutation(AccountMutation, TestMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
