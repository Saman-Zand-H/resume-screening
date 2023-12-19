from .exceptions import GraphQLError
from .utils import map_exception_to_error


class ErrorHandlingMiddleware:
    def resolve(self, next_resolver, root, info, **args):
        try:
            return next_resolver(root, info, **args)
        except Exception as e:
            base_exception = GraphQLError
            kwargs = {}

            if isinstance(e, GraphQLError):
                base_exception = e.__class__
                kwargs.update(e.as_dict())
            else:
                error = map_exception_to_error(e.__class__, str(e))
                kwargs.update({"error": error})
            kwargs.update({"exception": e})
            raise base_exception(**kwargs)
