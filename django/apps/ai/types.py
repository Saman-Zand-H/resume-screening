from collections.abc import Callable
from enum import Enum
from typing import Any, List, Union

from google.cloud import vision
from pydantic import BaseModel, ConfigDict


class FileType(Enum):
    IMAGE = "image"
    PDF = "pdf"


class CachableVectorStore(BaseModel):
    id: str
    """The identifier of the vector store."""

    data_fn: Callable[[], List[Any]]
    """The function that returns the data to be stored in the vector store."""

    cache_key: str
    """The cache key for the vector store."""


class FileToTextResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    file_type: FileType
    response: Union[vision.AnnotateImageResponse, vision.AnnotateFileResponse]
