from typing import ClassVar, Optional

from pydantic import BaseModel

from django.contrib.auth.models import Permission

from .utils import get_all_subclasses


class PermissionClass(BaseModel):
    name: ClassVar[str]
    description: ClassVar[Optional[str]] = None

    @classmethod
    def ensure_permissions_exist(cls):
        for subclass in get_all_subclasses(cls):
            name = getattr(subclass, "name")
            description = getattr(subclass, "description", None)
            Permission.objects.get_or_create(codename=name, defaults={"name": description or name})
