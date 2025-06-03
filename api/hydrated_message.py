from dataclasses import dataclass
from database import Database
from deferred_user import DeferredUser, DeferredUserFactory
from message import Message


@dataclass
class HydratedMessage:
    deferred_sender: DeferredUser
    content: str
    timestamp: int
    topic_name: str

    @staticmethod
    def create(
        *, message: Message, factory: DeferredUserFactory, database: Database
    ) -> "HydratedMessage":
        if message.type == "stream":
            topic_name = database.topic_table.get_topic(message.topic_id).name
        else:
            topic_name = ""

        return HydratedMessage(
            deferred_sender=factory.create_user(message.sender_id),
            content=message.content,
            timestamp=message.timestamp,
            topic_name=topic_name,
        )
