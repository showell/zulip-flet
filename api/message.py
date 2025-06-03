from pydantic import BaseModel
from typing import Any
from topic_table import TopicTable
from address import Address


class Message(BaseModel):
    id: int
    sender_id: int
    address: Address
    timestamp: int
    content: str

    @staticmethod
    def from_raw(raw_message: dict[str, Any], topic_table: TopicTable) -> "Message":
        display_recipient = raw_message["display_recipient"]
        if raw_message["type"] == "stream":
            user_ids = set()
            topic_id = topic_table.get_topic_id(
                raw_message["stream_id"], raw_message["subject"]
            )
        else:
            topic_id = 0
            user_ids = {recip["id"] for recip in display_recipient}

        address = Address(
            type=raw_message["type"], topic_id=topic_id, user_ids=user_ids
        )

        return Message(
            id=raw_message["id"],
            address=address,
            sender_id=raw_message["sender_id"],
            timestamp=raw_message["timestamp"],
            content=raw_message["content"],
        )

    def get_stream_id(self, topic_table: TopicTable) -> int:
        assert self.address.type == "stream"
        topic = topic_table.get_topic(self.address.topic_id)
        return topic.stream_id
