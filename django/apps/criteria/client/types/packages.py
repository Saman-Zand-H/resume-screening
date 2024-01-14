from typing import List

from pydantic import BaseModel, RootModel


class Package(BaseModel):
    id: str
    name: str


PackagesResponse = RootModel[List[Package]]
