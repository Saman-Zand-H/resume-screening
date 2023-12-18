from graphql import GraphQLError
from typing import Optional
from .errors import Error, Errors


class BaseGraphQLError(GraphQLError):
    error: Optional[Error] = Errors.INTERNAL_SERVER_ERROR
    code = None
    message = None

    def __init__(self, error: Error = None, extensions: dict = None):
        self.error = error or self.error
        self.code = self.error.code
        self.message = self.error.message

        if extensions is None:
            extensions = {}
        if "code" not in extensions:
            extensions["code"] = self.code
        super().__init__(message=self.message, extensions=extensions)
