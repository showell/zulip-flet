from dataclasses import dataclass
from user import User

@dataclass
class HydratedMessage:
    sender: User
    content: str
    timestamp: int

    @staticmethod
    async def create(*, message, service):
        return HydratedMessage(
            sender=await service.get_user(message.sender_id),
            content=message.content,
            timestamp=message.content,
        )