from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from .models import InAppNotification


class InAppNotificationNode(DjangoObjectType):
    class Meta:
        model = InAppNotification
        use_connection = True
        fields = (
            InAppNotification.id.field.name,
            InAppNotification.title.field.name,
            InAppNotification.body.field.name,
            InAppNotification.read_at.field.name,
            InAppNotification.created.field.name,
            InAppNotification.modified.field.name,
        )
        filter_fields = {
            InAppNotification.read_at.field.name: ["isnull"],
        }
