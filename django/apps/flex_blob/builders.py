import mimetypes
from datetime import datetime
from functools import lru_cache

from common.utils import get_all_subclasses

from django.conf import settings
from django.http.response import HttpResponseBase
from django.utils.http import http_date

from .models import FileModel

DJANGO_STORAGE_BACKEND = "django.core.files.storage.FileSystemStorage"


class BlobResponseBuilder:
    storage_backend: str

    @classmethod
    def get_content_type(cls, file_record: FileModel) -> str:
        return NotImplemented

    @classmethod
    def get_last_modified(cls, file_record: FileModel) -> int:
        return NotImplemented

    @classmethod
    def get_file_name(cls, file_record: FileModel) -> str:
        return NotImplemented

    @classmethod
    def get_content_length(cls, file_record: FileModel) -> int:
        return NotImplemented

    @classmethod
    @lru_cache
    def get_response_builder(cls):
        current_storage = getattr(settings, "STORAGES", {}).get("default", {}).get("BACKEND") or DJANGO_STORAGE_BACKEND

        return next(
            (subclass for subclass in get_all_subclasses(cls) if subclass.storage_backend == current_storage),
            DefaultStorageResponseBuilder,
        )

    @classmethod
    def build_response[T: HttpResponseBase](cls, file_record: FileModel, base_response: T) -> T:
        response_builder = cls.get_response_builder()

        base_response["Content-Type"] = response_builder.get_content_type(file_record)
        base_response["Last-Modified"] = http_date(response_builder.get_last_modified(file_record))
        base_response["Content-Disposition"] = f'inline; filename="{response_builder.get_file_name(file_record)}"'
        base_response["Content-Length"] = response_builder.get_content_length(file_record)

        return base_response


class DefaultStorageResponseBuilder(BlobResponseBuilder):
    storage_backend = DJANGO_STORAGE_BACKEND

    @classmethod
    def get_content_type(cls, file_record: FileModel):
        return mimetypes.guess_type(file_record.file.file.name)[0]

    @classmethod
    def get_last_modified(cls, file_record: FileModel):
        return datetime.now().timestamp()

    @classmethod
    def get_file_name(cls, file_record: FileModel):
        return file_record.file.file.name

    @classmethod
    def get_content_length(cls, file_record: FileModel):
        return file_record.file.size


class GoogleStorageResponseBuilder(DefaultStorageResponseBuilder):
    storage_backend = "storages.backends.gcloud.GoogleCloudStorage"

    @classmethod
    def get_content_type(cls, file_record: FileModel):
        return file_record.file.file.mime_type

    @classmethod
    def get_last_modified(cls, file_record: FileModel):
        return file_record.file.file.flex_blob.updated.timestamp()
