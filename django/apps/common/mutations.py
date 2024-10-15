import graphene
from graphene_file_upload.scalars import Upload
from graphql_jwt.decorators import login_required

from .types import UploadType, AnalysableUploadType
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
        temporary_obj = model.get_user_temporary_file(user)

        if temporary_obj:
            obj = temporary_obj.update_temporary_file(file)
        else:
            obj = model.create_temporary_file(file=file, user=user)

        return cls(pk=obj.pk)


class AnalyseAndExtractFileDataMutation(graphene.Mutation):
    is_valid = graphene.Boolean()
    data = graphene.JSONString()

    class Arguments:
        type = AnalysableUploadType(required=True)
        file_id = graphene.String(required=True)

    @staticmethod
    def mutate(root, info, type, file_id):
        return AnalyseAndExtractFileDataMutation(is_valid=True, data={})


class CommonMutation(graphene.ObjectType):
    upload_file = UploadFileMutation.Field()
    get_file_data = AnalyseAndExtractFileDataMutation.Field()


class Mutation(graphene.ObjectType):
    common = graphene.Field(CommonMutation, required=True)

    def resolve_common(self, *args, **kwargs):
        return CommonMutation()
