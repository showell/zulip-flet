from pydantic import BaseModel


class Topic(BaseModel):
    stream_id: int
    name: str

    def key(self) -> str:
        return f"{self.stream_id},{self.name}"
