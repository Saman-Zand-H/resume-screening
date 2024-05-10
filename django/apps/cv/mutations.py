import graphene
from graphql_jwt.decorators import login_required

from .tasks import render_cv_template


class GenerateResumeMutation(graphene.Mutation):
    class Arguments:
        template_id = graphene.ID()

    success = graphene.Boolean()

    @login_required
    @staticmethod
    def mutate(root, info, template_id):
        user = info.context.user
        render_cv_template.delay(user.pk, template_id)
        
        return GenerateResumeMutation(success=True)


class CVMutation(graphene.ObjectType):
    generate_resume = GenerateResumeMutation.Field()


class Mutation(graphene.ObjectType):
    cv = graphene.Field(CVMutation, required=True)

    def resolve_cv(self, info):
        return CVMutation()
