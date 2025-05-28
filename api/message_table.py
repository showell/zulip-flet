from pydantic import BaseModel

from message import Message

class MessageTable(BaseModel):
    table: dict[int, Message] = {}

    def get_rows(self):
        return self.table.values()

    def insert(self, message: Message):
        self.table[message.id] = message

    def insert_many(self, raw_messages):
        for message in raw_messages:
            self.insert(Message.from_raw(message))
