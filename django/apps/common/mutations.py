import graphene
from graphene_file_upload.scalars import Upload

from .decorators import login_required
from .types import UploadType
from .utils import get_file_model


@login_required
class UploadFileMutation(graphene.Mutation):
    class Arguments:
        type = UploadType(required=True)
        file = Upload(required=True)

    pk = graphene.Int()

    @classmethod
    def mutate(cls, root, info, file, type):
        user = info.context.user
        model = get_file_model(type.value)
        temporary_obj = model.get_user_temporary_file(user)

        if temporary_obj:
            obj = temporary_obj.update_temporary_file(file)
        else:
            obj = model.create_temporary_file(file=file, user=user)

        return cls(pk=obj.pk)


class CommonMutation(graphene.ObjectType):
    upload_file = UploadFileMutation.Field()


class Mutation(graphene.ObjectType):
    common = graphene.Field(CommonMutation, required=True)

    def resolve_common(self, *args, **kwargs):
        return CommonMutation()
