from typing import Any

from address import Address
from message_parser import get_message_node
from pydantic import BaseModel
from topic_table import TopicTable


def fix_content(content: str) -> str:
    host = "https://chat.zulip.org"
    if "/user_uploads" in content:
        content = content.replace("/user_uploads", host + "/user_uploads")
    return content


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

        content = fix_content(raw_message["content"])

        get_message_node(content)  # for validation

        return Message(
            id=raw_message["id"],
            address=address,
            sender_id=raw_message["sender_id"],
            timestamp=raw_message["timestamp"],
            content=content,
        )

    def get_stream_id(self, topic_table: TopicTable) -> int:
        assert self.address.type == "stream"
        topic = topic_table.get_topic(self.address.topic_id)
        return topic.stream_id
