from message import Message


class SentByFilter:
    def __init__(self, sender_id):
        self.sender_id = sender_id

    def get_rows(self, all_messages: list[Message]) -> list[Message]:
        return [m for m in all_messages if m.sender_id == self.sender_id]
