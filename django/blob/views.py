import datetime
import mimetypes

from storages.backends.gcloud import GoogleCloudFile

from django.core.files.base import File
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

FILE_RESPONSE = {
    File: {
        "content_type": lambda file: mimetypes.guess_type(file.name)[0],
        "last_modified": lambda _: http_date(datetime.datetime.now().timestamp()),
    },
    GoogleCloudFile: {
        "content_type": lambda file: file.mime_type,
        "last_modified": lambda file: http_date(file.blob.updated.timestamp()),
    },
}


class MediaAuthorizationView(View):
    def get(self, request: HttpRequest, path: str):
        if not path:
            return HttpResponseBadRequest(_("Invalid file path."))

        try:
            file_record = BaseFileModel.objects.get(file=path)
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

        meta_data = FILE_RESPONSE.get(type(file_record.file.file), {})
        response = StreamingHttpResponse(
            file_iterator(),
            content_type=meta_data.get("content_type")(file_record.file.file),
        )
        response["Last-Modified"] = meta_data.get("last_modified")(file_record.file.file)
        response["Content-Disposition"] = f'inline; filename="{file_record.file.name}"'
        response["Content-Length"] = file_record.file.size
        return response
