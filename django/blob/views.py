from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    StreamingHttpResponse,
)
from django.utils.http import http_date
from django.utils.translation import gettext_lazy as _
from django.views import View

from .models import BaseFileModel


class MediaAuthorizationView(View):
    def get(self, request: HttpRequest, file_path: str):
        if not file_path:
            return HttpResponseBadRequest(_("Invalid file path."))

        try:
            file_record = BaseFileModel.objects.get(file=file_path)
        except BaseFileModel.DoesNotExist:
            return HttpResponseNotFound(_("File not found."))

        if not file_record.check_auth(request):
            return HttpResponseForbidden(_("You are not authorized to access this file."))

        return self.serve_file(file_record)

    def serve_file(self, file_record: BaseFileModel, chunk_size: int = 8192):
        def file_iterator():
            with file_record.file.open("rb") as file_obj:
                while chunk := file_obj.read(chunk_size):
                    yield chunk

        response = StreamingHttpResponse(file_iterator(), content_type=file_record.file.file.content_type)
        response["Content-Disposition"] = f'inline; filename="{file_record.file.name}"'
        response["Content-Length"] = file_record.file.size
        response["Last-Modified"] = http_date(file_record.file.modified.timestamp())
        return response
