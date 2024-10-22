import graphene
from common.utils import fields_join
from graphene_django_cud.mutations import DjangoBatchPatchMutation
from graphql_jwt.decorators import login_required
from graphql_jwt.refresh_token.models import RefreshToken as UserRefreshToken

from django.utils import timezone
from notification.models import InAppNotification, UserPushNotificationToken

from .models import UserDevice


class InAppNotificationReadAtUpdateMutation(DjangoBatchPatchMutation):
    class Meta:
        model = InAppNotification
        login_required = True
        fields = (InAppNotification.id.field.name,)
        type_name = "InAppNotificationReadAtUpdateInput"

    @classmethod
    def before_mutate(cls, root, info, input):
        ids = [item["id"] for item in input]
        not_set_ids = InAppNotification.objects.filter(id__in=ids, read_at__isnull=True).values_list("id", flat=True)
        for item in input:
            if int(item["id"]) in not_set_ids:
                item["read_at"] = timezone.now()
        return super().before_mutate(root, info, input)


class InAppNotificationMutation(graphene.ObjectType):
    update_read_at = InAppNotificationReadAtUpdateMutation.Field()


class RegisterPushNotificationTokenMutation(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)

    success = graphene.Boolean()

    @login_required
    def mutate(root, info, token):
        user_device = info.context.user_device
        if not user_device:
            return RegisterPushNotificationTokenMutation(success=False)
        UserPushNotificationToken.objects.update_or_create(
            device=user_device,
            defaults={UserPushNotificationToken.token.field.name: token},
            create_defaults={UserPushNotificationToken.token.field.name: token},
        )
        return RegisterPushNotificationTokenMutation(success=True)


class RemovePushNotificationTokenMutation(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)

    success = graphene.Boolean()

    @login_required
    def mutate(root, info, token):
        user = info.context.user
        UserPushNotificationToken.objects.filter(
            **{
                UserPushNotificationToken.token.field.name: token,
                fields_join(
                    UserPushNotificationToken.device.field.name,
                    UserDevice.refresh_token.field.name,
                    UserRefreshToken.user.field.name,
                ): user,
            }
        ).delete()
        return RemovePushNotificationTokenMutation(success=True)


class PushNotificationMutation(graphene.ObjectType):
    register_token = RegisterPushNotificationTokenMutation.Field()
    remove_token = RemovePushNotificationTokenMutation.Field()


class NotificationMutation(graphene.ObjectType):
    in_app_notification = graphene.Field(InAppNotificationMutation)
    push_notification = graphene.Field(PushNotificationMutation)

    def resolve_in_app_notification(self, info):
        return InAppNotificationMutation()

    def resolve_push_notification(self, *args, **kwargs):
        return PushNotificationMutation()


class Mutation(graphene.ObjectType):
    notification = graphene.Field(NotificationMutation, required=True)

    def resolve_notification(self, info):
        return NotificationMutation()
