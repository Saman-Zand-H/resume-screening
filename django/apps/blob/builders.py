import mimetypes
from abc import abstractmethod
from datetime import datetime

from common.utils import get_all_subclasses

from django.conf import settings
from django.http.response import HttpResponseBase
from django.utils.http import http_date

from .models import BaseFileModel


class BlobResponseBuilder:
    storage_backend: str

    @property
    @abstractmethod
    def content_type(self, file_record: BaseFileModel) -> str:
        return NotImplemented

    @property
    @abstractmethod
    def last_modified(self, file_record: BaseFileModel) -> int:
        return NotImplemented

    @property
    @abstractmethod
    def file_name(self, file_record: BaseFileModel) -> str:
        return NotImplemented

    @property
    @abstractmethod
    def content_length(self, file_record: BaseFileModel) -> int:
        return NotImplemented

    @classmethod
    def get_response_builder(cls):
        return next(
            (
                subclass
                for subclass in get_all_subclasses(cls)
                if subclass.storage_backend == settings.DEFAULT_FILE_STORAGE
            ),
            DefaultStorageResponseBuilder,
        )

    @classmethod
    def build_response[T: HttpResponseBase](cls, file_record: BaseFileModel, base_response: T) -> T:
        response_builder = cls.get_response_builder()

        base_response["Content-Type"] = response_builder.content_type(file_record)
        base_response["Last-Modified"] = http_date(response_builder.last_modified(file_record))
        base_response["Content-Disposition"] = f'inline; filename="{response_builder.file_name(file_record)}"'
        base_response["Content-Length"] = response_builder.content_length(file_record)

        return base_response


class DefaultStorageResponseBuilder(BlobResponseBuilder):
    storage_backend = "django.core.files.storage.FileSystemStorage"

    def content_type(self, file_record: BaseFileModel):
        return mimetypes.guess_type(file_record.file.file.name)[0]

    def last_modified(self, file_record: BaseFileModel):
        return datetime.now().timestamp()

    def file_name(self, file_record: BaseFileModel):
        return file_record.file.file.name

    def content_length(self, file_record: BaseFileModel):
        return file_record.file.size


class GoogleStorageResponseBuilder(DefaultStorageResponseBuilder):
    storage_backend = "storages.backends.gcloud.GoogleCloudStorage"

    def content_type(self, file_record: BaseFileModel):
        return file_record.file.file.mime_type

    def last_modified(self, file_record: BaseFileModel):
        return file_record.file.file.blob.updated.timestamp()
