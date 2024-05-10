from graphql_jwt.middleware import _authenticate

from django.contrib.auth import authenticate
from django.utils.deprecation import MiddlewareMixin


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if _authenticate(request):
            request.user = authenticate(request)
