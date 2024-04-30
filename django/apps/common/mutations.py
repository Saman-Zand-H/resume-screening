import graphene
from graphene_file_upload.scalars import Upload
from graphql_jwt.decorators import login_required

from .types import UploadType
from .utils import get_file_model


class UploadFileMutation(graphene.Mutation):
    class Arguments:
        type = UploadType(required=True)
        file = Upload(required=True)

    pk = graphene.Int()

    @classmethod
    @login_required
    def mutate(cls, root, info, file, type):
        user = info.context.user
        model = get_file_model(type.value)
        temprorary_obj = model.get_user_temprorary_file(user)

        obj = None
        if temprorary_obj:
            obj = temprorary_obj.update_temporary_file(file)
        else:
            obj = model.objects.create_temporary_file(file=file, user=user)

        return UploadFileMutation(pk=obj.pk)


class CommonMutation(graphene.ObjectType):
    upload_file = UploadFileMutation.Field()


class Mutation(graphene.ObjectType):
    common = graphene.Field(CommonMutation, required=True)

    def resolve_common(self, *args, **kwargs):
        return CommonMutation()
