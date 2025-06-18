from typing import Any

from pydantic import BaseModel


class Stream(BaseModel):
    id: int
    name: str

    @staticmethod
    def from_raw(raw_stream: dict[str, Any]) -> "Stream":
        return Stream(
            id=raw_stream["stream_id"],
            name=raw_stream["name"],
        )
