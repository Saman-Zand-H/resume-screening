import graphene
from common.decorators import login_required
from common.utils import fj
from graphene_django_cud.mutations import DjangoBatchPatchMutation

from django.db.models.lookups import In, IsNull
from django.utils import timezone
from notification.models import InAppNotification, UserPushNotificationToken


@login_required
class InAppNotificationReadAtUpdateMutation(DjangoBatchPatchMutation):
    class Meta:
        model = InAppNotification
        login_required = True
        fields = (InAppNotification.id.field.name,)
        type_name = "InAppNotificationReadAtUpdateInput"

    @classmethod
    def before_mutate(cls, root, info, input):
        ids = [item["id"] for item in input]
        notifications = InAppNotification.objects.filter(
            **{
                fj(InAppNotification._meta.pk.attname, In.lookup_name): ids,
                fj(InAppNotification.user): info.context.user,
                fj(InAppNotification.read_at, IsNull.lookup_name): True,
            }
        )

        if notifications.exists():
            notifications.update(**{fj(InAppNotification.read_at): timezone.now()})

        return super().before_mutate(root, info, input)


class InAppNotificationMutation(graphene.ObjectType):
    update_read_at = InAppNotificationReadAtUpdateMutation.Field()


@login_required
class RegisterPushNotificationTokenMutation(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)

    success = graphene.Boolean()

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


class PushNotificationMutation(graphene.ObjectType):
    register_token = RegisterPushNotificationTokenMutation.Field()


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
