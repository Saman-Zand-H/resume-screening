from typing import ClassVar, List, Optional, Type

from pydantic import BaseModel

from .utils import get_all_subclasses


class Rule(BaseModel):
    name: ClassVar[str]
    description: ClassVar[Optional[str]] = None

    @classmethod
    def get_rules(cls) -> List[Type["Rule"]]:
        return get_all_subclasses(cls)
