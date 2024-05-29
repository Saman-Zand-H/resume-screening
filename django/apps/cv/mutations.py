import graphene
from account.tasks import user_task_runner
from graphql_jwt.decorators import login_required

from .tasks import render_cv_template


class GenerateResumeMutation(graphene.Mutation):
    class Arguments:
        template_id = graphene.ID(required=False)

    success = graphene.Boolean()

    @staticmethod
    @login_required
    def mutate(root, info, template_id=None):
        user = info.context.user
        user_task_runner(render_cv_template, task_user_id=user.pk, user_id=user.pk, template_id=template_id)
        return GenerateResumeMutation(success=False)


class CVMutation(graphene.ObjectType):
    generate_resume = GenerateResumeMutation.Field()


class Mutation(graphene.ObjectType):
    cv = graphene.Field(CVMutation, required=True)

    def resolve_cv(self, info):
        return CVMutation()
