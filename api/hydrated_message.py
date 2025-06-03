from dataclasses import dataclass
from address import Address
from database import Database
from deferred_user import DeferredUser, DeferredUserFactory
from message import Message


@dataclass
class HydratedMessage:
    deferred_sender: DeferredUser
    content: str
    timestamp: int
    address: Address
    address_name: str

    @staticmethod
    def create(
        *, message: Message, factory: DeferredUserFactory, database: Database
    ) -> "HydratedMessage":
        return HydratedMessage(
            deferred_sender=factory.create_user(message.sender_id),
            content=message.content,
            timestamp=message.timestamp,
            address=message.address,
            address_name=message.address.name(
                topic_table=database.topic_table, user_table=database.user_table
            ),
        )
