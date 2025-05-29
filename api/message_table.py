from pydantic import BaseModel

from message import Message


class MessageTable(BaseModel):
    table: dict[int, Message] = {}

    def get_rows(self) -> list[Message]:
        return list(self.table.values())

    def insert(self, row: Message) -> None:
        self.table[row.id] = row
