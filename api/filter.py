from address import Address
from message import Message


class DirectMessageFilter:
    def __init__(self, *, user_id: int) -> None:
        self.user_id = user_id

    def get_rows(self, all_messages: list[Message]) -> list[Message]:
        return [m for m in all_messages if self.user_id in m.address.user_ids]


class SentByFilter:
    def __init__(self, sender_id: int) -> None:
        self.sender_id = sender_id

    def get_rows(self, all_messages: list[Message]) -> list[Message]:
        return [m for m in all_messages if m.sender_id == self.sender_id]


class TopicFilter:
    def __init__(self, *, topic_id: int) -> None:
        self.topic_id = topic_id

    def get_rows(self, all_messages: list[Message]) -> list[Message]:
        return [m for m in all_messages if m.address.topic_id == self.topic_id]


class AddressFilter:
    def __init__(self, address: Address) -> None:
        self.address = address

    def get_rows(self, all_messages: list[Message]) -> list[Message]:
        return [m for m in all_messages if m.address == self.address]
