from dataclasses import dataclass
from deferred_user import DeferredUser, DeferredUserFactory
from message import Message


@dataclass
class HydratedMessage:
    deferred_sender: DeferredUser
    content: str
    timestamp: int

    @staticmethod
    def create(*, message: Message, factory: DeferredUserFactory) -> "HydratedMessage":
        return HydratedMessage(
            deferred_sender=factory.create_user(message.sender_id),
            content=message.content,
            timestamp=message.timestamp,
        )
