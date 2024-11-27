import graphene
from common.utils import fields_join
from graphene_django_cud.mutations import DjangoBatchPatchMutation
from graphql_jwt.decorators import login_required

from django.db.models.lookups import In, IsNull
from django.utils import timezone
from notification.models import InAppNotification, UserPushNotificationToken


class InAppNotificationReadAtUpdateMutation(DjangoBatchPatchMutation):
    class Meta:
        model = InAppNotification
        login_required = True
        fields = (InAppNotification.id.field.name,)
        type_name = "InAppNotificationReadAtUpdateInput"

    @classmethod
    def before_mutate(cls, root, info, input):
        ids = [item["id"] for item in input]
        not_set_ids = InAppNotification.objects.filter(
            **{
                fields_join(InAppNotification._meta.pk.attname, In.lookup_name): ids,
                fields_join(InAppNotification.read_at, IsNull.lookup_name): True,
            }
        ).values_list("id", flat=True)
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
