from dataclasses import dataclass
from database import Database
from deferred_user import DeferredUser, DeferredUserFactory
from message import Message


@dataclass
class HydratedMessage:
    deferred_sender: DeferredUser
    content: str
    timestamp: int
    address_name: str

    @staticmethod
    def create(
        *, message: Message, factory: DeferredUserFactory, database: Database
    ) -> "HydratedMessage":
        if message.address.type == "stream":
            address_name = database.topic_table.get_topic(message.address.topic_id).name
        else:
            address_name = ""

        return HydratedMessage(
            deferred_sender=factory.create_user(message.sender_id),
            content=message.content,
            timestamp=message.timestamp,
            address_name=address_name,
        )
