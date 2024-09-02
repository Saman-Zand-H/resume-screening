import graphene
from graphene_django_cud.mutations import DjangoBatchPatchMutation
from django.utils import timezone

from .models import InAppNotification


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


class NotificationMutation(graphene.ObjectType):
    in_app_notification = graphene.Field(InAppNotificationMutation)

    def resolve_in_app_notification(self, info):
        return InAppNotificationMutation()


class Mutation(graphene.ObjectType):
    notification = graphene.Field(NotificationMutation, required=True)

    def resolve_notification(self, info):
        return NotificationMutation()
