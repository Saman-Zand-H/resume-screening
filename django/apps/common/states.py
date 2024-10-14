from common.exceptions import GraphQLErrorBadRequest


class ChangeStateMixin:
    def change_status(self, new_status, state_mapping, status_field, **kwargs):
        status = getattr(self, status_field)
        current_state = state_mapping.get(status)
        if not current_state:
            raise GraphQLErrorBadRequest(f"Invalid status: {status}")
        current_state.change_status(self, new_status, status_field, **kwargs)
        self.save(update_fields=[status_field])


class GenericState:
    new_statuses = []

    @classmethod
    def change_status(cls, obj, new_status, status_field, **kwargs):
        if new_status.value not in cls.new_statuses:
            raise GraphQLErrorBadRequest(f"Cannot transition from {cls} to {new_status.value}")

        setattr(obj, status_field, new_status.value)
        return obj.set_status_history()
