from graphql_jwt.middleware import _authenticate, get_http_authorization

from django.contrib.auth import authenticate
from django.http.response import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

from .models import UserDevice


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user = _authenticate(request) and authenticate(request) or request.user


class DeviceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not (get_http_authorization(request) and request.user.is_authenticated):
            request.user_device = None
            return

        device_id = request.headers.get("x-cpj-device-id")
        if not device_id:
            return HttpResponseForbidden()

        try:
            request.user_device = UserDevice.objects.get(device_id=device_id)
        except UserDevice.DoesNotExist:
            return HttpResponseForbidden()
