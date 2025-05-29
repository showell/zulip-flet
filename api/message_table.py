from pydantic import BaseModel

from message import Message


class MessageTable(BaseModel):
    table: dict[int, Message] = {}

    def get_rows(self):
        return self.table.values()

    def insert(self, row: Message):
        self.table[row.id] = row
