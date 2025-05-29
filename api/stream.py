from pydantic import BaseModel


class Stream(BaseModel):
    id: int
    name: str

    @staticmethod
    def from_raw(raw_stream):
        return Stream(
            id=raw_stream["stream_id"],
            name=raw_stream["name"],
        )
