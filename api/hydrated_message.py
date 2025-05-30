from dataclasses import dataclass
from user import User


@dataclass
class HydratedMessage:
    sender: User
    content: str
    timestamp: int

    @staticmethod
    def create(*, message, service):
        return HydratedMessage(
            sender=service.get_local_user(message.sender_id),
            content=message.content,
            timestamp=message.content,
        )
