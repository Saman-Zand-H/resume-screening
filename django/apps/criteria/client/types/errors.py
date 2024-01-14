from typing import Optional

from pydantic import BaseModel, model_validator


class Error(BaseModel):
    message: Optional[str] = None
    code: Optional[str] = None

    @model_validator(mode="before")
    def check_at_least_one(cls, values):
        if not values.get("message") and not values.get("code"):
            raise ValueError("At least one of 'message' or 'code' must be provided.")
        return values
