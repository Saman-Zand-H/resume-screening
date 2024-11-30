from common.utils import fj
from graphql_jwt.middleware import _authenticate, get_http_authorization
from graphql_jwt.refresh_token.models import RefreshToken

from django.contrib.auth import authenticate
from django.http.response import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

from .models import UserDevice


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user = _authenticate(request) and authenticate(request) or request.user


class DeviceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user_device = None
        if not (get_http_authorization(request) and request.user.is_authenticated):
            return

        device_id = request.headers.get("x-cpj-device-id")
        if not device_id:
            return HttpResponseForbidden()

        try:
            request.user_device = UserDevice.objects.get(
                **{
                    UserDevice.device_id.field.name: device_id,
                    fj(UserDevice.refresh_token, RefreshToken.user): request.user,
                }
            )
        except UserDevice.DoesNotExist:
            return HttpResponseForbidden()
