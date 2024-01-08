from enum import Enum


class FileType(Enum):
    IMAGE = "image"
    PDF = "pdf"


FILE_TYPE_MAPPING = {
    "image/": FileType.IMAGE,
    "application/pdf": FileType.PDF,
}
