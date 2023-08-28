import graphene


class PingQuery(graphene.ObjectType):
    ping = graphene.String()

    def resolve_ping(self, info):
        return "pong"


class Query(PingQuery):
    pass
