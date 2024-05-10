from graphql_jwt.middleware import _authenticate

from django.contrib.auth import authenticate
from django.utils.deprecation import MiddlewareMixin


class AuthMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        if _authenticate(request):
            request.user = authenticate(request)
        return self.get_response(request)
