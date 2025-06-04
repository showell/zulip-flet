from pydantic import BaseModel
from stream_table import StreamTable

class Topic(BaseModel):
    stream_id: int
    name: str

    def key(self) -> str:
        return f"{self.stream_id},{self.name}"

    def label(self, *, stream_table: StreamTable) -> str:
        stream = stream_table.get_row(self.stream_id)
        return f"{stream.name}: {self.name}"
