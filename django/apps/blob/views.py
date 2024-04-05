from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    StreamingHttpResponse,
)
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.static import serve

from .builders import BlobResponseBuilder
from .models import FileModel


class MediaAuthorizationView(View):
    def get(self, request: HttpRequest, path: str):
        if not path:
            return HttpResponseBadRequest(_("Invalid file path."))

        if not (file_record := FileModel.objects.filter(file=path).first()):
            return serve(request, path, document_root=settings.MEDIA_ROOT)

        if not file_record.check_auth(request):
            return HttpResponseForbidden(_("You are not authorized to access this file."))

        return self.serve_file(file_record)

    def serve_file(self, file_record: FileModel, chunk_size: int = 8192):
        def file_iterator():
            with file_record.file.open("rb") as file_obj:
                while chunk := file_obj.read(chunk_size):
                    yield chunk

        response = StreamingHttpResponse(file_iterator())
        return BlobResponseBuilder.build_response(file_record, response)
