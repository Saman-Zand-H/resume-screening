from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    StreamingHttpResponse,
)
from django.utils.translation import gettext_lazy as _

from .models import BaseFileModel


class MediaAuthorizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if not request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        if not (file_path := request.path.replace(settings.MEDIA_URL, "")):
            return HttpResponseBadRequest(_("Invalid file path."))

        try:
            base_file = BaseFileModel.objects.get(file=file_path)
        except BaseFileModel.DoesNotExist:
            return HttpResponseNotFound(_("File not found."))

        if not base_file.check_auth(request):
            return HttpResponseForbidden(_("You are not authorized to access this file."))

        return self.serve_file(base_file)

    def serve_file(self, base_file: BaseFileModel):
        def file_iterator():
            with base_file.file.open("rb") as file_obj:
                while chunk := file_obj.read(8192):
                    yield chunk

        response = StreamingHttpResponse(file_iterator(), content_type=base_file.file.file.content_type)
        response["Content-Disposition"] = f'inline; filename="{base_file.file.name}"'
        response["Content-Length"] = base_file.file.size
        return response
