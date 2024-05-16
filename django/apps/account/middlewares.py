from graphql_jwt.middleware import _authenticate

from django.contrib.auth import authenticate
from django.utils.deprecation import MiddlewareMixin


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user = _authenticate(request) and authenticate(request) or request.user
