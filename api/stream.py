from pydantic import BaseModel
from typing import Any


class Stream(BaseModel):
    id: int
    name: str

    @staticmethod
    def from_raw(raw_stream: dict[str, Any]) -> "Stream":
        return Stream(
            id=raw_stream["stream_id"],
            name=raw_stream["name"],
        )
