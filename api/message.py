from pydantic import BaseModel


class Message(BaseModel):
    id: int
    type: str
    sender_id: int
    stream_id: int
    user_ids: set
    topic: str
    timestamp: int
    flags: list[str]
    content: str

    @staticmethod
    def from_raw(raw_message):
        display_recipient = raw_message["display_recipient"]
        if raw_message["type"] == "stream":
            stream_id = raw_message["stream_id"]
            user_ids = set()
        else:
            stream_id = 0
            print(display_recipient)
            user_ids = {recip["id"] for recip in display_recipient}

        return Message(
            id=raw_message["id"],
            type=raw_message["type"],
            sender_id=raw_message["sender_id"],
            stream_id=stream_id,
            user_ids=user_ids,
            topic=raw_message["subject"],
            timestamp=raw_message["timestamp"],
            flags=raw_message["flags"],
            content=raw_message["content"],
        )


