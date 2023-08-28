import graphene


class Sum(graphene.Mutation):
    class Arguments:
        number1 = graphene.Int(required=True)
        number2 = graphene.Int(required=True)

    result = graphene.Int(required=True)

    @classmethod
    def mutate(cls, *_, number1, number2):
        return cls(result=number1 + number2)


class Mutation(graphene.ObjectType):
    sum = Sum.Field()
