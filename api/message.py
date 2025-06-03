from pydantic import BaseModel
from typing import Any
from topic_table import TopicTable

class Message(BaseModel):
    id: int
    type: str
    sender_id: int
    stream_id: int
    user_ids: set[int]
    topic_id: int
    timestamp: int
    flags: list[str]
    content: str

    @staticmethod
    def from_raw(raw_message: dict[str, Any], topic_table: TopicTable) -> "Message":
        display_recipient = raw_message["display_recipient"]
        if raw_message["type"] == "stream":
            stream_id = raw_message["stream_id"]
            user_ids = set()
            topic_id = topic_table.get_topic_id(stream_id, raw_message["subject"])
        else:
            stream_id = 0
            topic_id = 0
            user_ids = {recip["id"] for recip in display_recipient}

        return Message(
            id=raw_message["id"],
            type=raw_message["type"],
            sender_id=raw_message["sender_id"],
            stream_id=stream_id,
            user_ids=user_ids,
            topic_id=topic_id,
            timestamp=raw_message["timestamp"],
            flags=raw_message["flags"],
            content=raw_message["content"],
        )
