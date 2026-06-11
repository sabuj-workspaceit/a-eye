from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    message: str = ""
    status: bool
    data: T | None = None
    errors: Any | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
