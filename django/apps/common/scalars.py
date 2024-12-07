import graphene

from common.exceptions import GraphQLErrorBadRequest
from django.utils.translation import gettext as _


class NotEmptyID(graphene.ID):
    @staticmethod
    def check_id(value):
        if value == "":
            raise GraphQLErrorBadRequest(_("ID cannot be empty"))

    @staticmethod
    def parse_value(value):
        NotEmptyID.check_id(value)
        return super().parse_value(value)

    @staticmethod
    def parse_literal(node):
        NotEmptyID.check_id(node.value)
        return super().parse_literal(node)
