from collections.abc import Callable
from typing import Any, List

from pydantic import BaseModel


class CachableVectorStore(BaseModel):
    id: str
    """The identifier of the vector store."""

    data_fn: Callable[[], List[Any]]
    """The function that returns the data to be stored in the vector store."""

    cache_key: str
    """The cache key for the vector store."""
