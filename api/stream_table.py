from pydantic import BaseModel

from stream import Stream


class StreamTable(BaseModel):
    table: dict[int, Stream] = {}

    def insert(self, row: Stream) -> None:
        self.table[row.id] = row
