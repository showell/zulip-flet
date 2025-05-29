import data_layer
from database import Database
from message import Message
from user import User
from hydrated_message import HydratedMessage


class Service:
    def __init__(self, database: Database):
        self.database = database

    async def get_users(self) -> list[User]:
        return self.database.user_table.get_rows()

    async def get_user(self, user_id: int) -> User:
        return self.database.user_table.get_row(user_id)

    async def get_messages_sent_by_user(self, user: User) -> list[Message]:
        all_messages = self.database.message_table.get_rows()
        messages = [m for m in all_messages if m.sender_id == user.id]
        hydrated_messages = [(await HydratedMessage.create(message=m, service=self)) for m in messages]
        return sorted(hydrated_messages, key=lambda m: m.timestamp)


async def get_service() -> Service:
    database = await data_layer.get_database()
    return Service(database)
